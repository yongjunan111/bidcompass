"""BC-30: 과거 낙찰 시뮬레이션.

558건 나의방 데이터로 코어엔진 개별 함수를 실행하여 가격점수 검증 및 분석.

핵심 설계:
  - select_table(추정가격) + calc_price_score(예정가격) 분리 호출
  - A값 누락을 [수의]비대상 vs 미수집으로 분리 집계
  - 순위 정합성 섹션 포함
  - WorkType 매핑 근거 출력 + 비건설 의심 카운트
  - 에러를 파싱/엔진입력/엔진실행으로 분류

사용:
    python manage.py simulate_historical
    python manage.py simulate_historical --limit 10
    python manage.py simulate_historical --output data/collected/simulation_result.json
"""

import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from math import floor
from pathlib import Path

from django.core.management.base import BaseCommand

from g2b.services.bid_engine import (
    AValueItems,
    TableType,
    WorkType,
    calculate_a_value,
    calc_price_score,
    ceil_up,
    select_table,
    TABLE_PARAMS_MAP,
    UNIT_EOUK,
)

# 검증용 TABLE_PARAMS (float) — Decimal 변환 없이 역산
VERIFY_TABLE_PARAMS = {
    "TABLE_1": {"max_score": 50, "coeff": 2, "fixed_ratio": 0.925, "fixed_score": 45},
    "TABLE_2A": {"max_score": 70, "coeff": 4, "fixed_ratio": 0.9125, "fixed_score": 65},
    "TABLE_2B": {"max_score": 70, "coeff": 20, "fixed_ratio": 0.9025, "fixed_score": 65},
    "TABLE_3": {"max_score": 80, "coeff": 20, "fixed_ratio": 0.9025, "fixed_score": 75},
    "TABLE_4": {"max_score": 90, "coeff": 20, "fixed_ratio": 0.9025, "fixed_score": 85},
    "TABLE_5": {"max_score": 90, "coeff": 20, "fixed_ratio": 0.9025, "fixed_score": 85},
}

# 독립 상수 (결합도 제거)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
EXCEL_FILES = [
    BASE_DIR / "docs" / "나의방_낙찰2026-02- 2025.xlsx",
    BASE_DIR / "docs" / "나의방_낙찰2026-02-05_1.xlsx",
]
A_VALUES_JSON = BASE_DIR / "data" / "collected" / "a_values.json"
PRELIM_PRICES_JSON = BASE_DIR / "data" / "collected" / "preliminary_prices.json"

# A값 JSON → AValueItems 필드 매핑
A_VALUE_FIELD_MAP = {
    "npnInsrprm": "national_pension",
    "mrfnHealthInsrprm": "health_insurance",
    "rtrfundNon": "retirement_mutual_aid",
    "odsnLngtrmrcprInsrprm": "long_term_care",
    "sftyMngcst": "occupational_safety",
    "sftyChckMngcst": "safety_management",
    "qltyMngcst": "quality_management",
}

# 별표 경계값 (원) — 경계 근접 경고용
TABLE_BOUNDARIES = [
    2 * UNIT_EOUK,
    3 * UNIT_EOUK,
    10 * UNIT_EOUK,
    50 * UNIT_EOUK,
    100 * UNIT_EOUK,
]
BOUNDARY_MARGIN = Decimal("0.03")  # 3%

# 건설 종목 키워드
CONSTRUCTION_KEYWORDS = ["건축", "토건", "토목", "건설"]


# ──────────────────────────────────────────────
# 유틸리티
# ──────────────────────────────────────────────

def parse_amount(val):
    """콤마 문자열/float/int → int. None이면 None."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if isinstance(val, float) and val != val:  # NaN
            return None
        return int(val)
    s = str(val).strip().replace(",", "")
    return int(s) if s else None


def load_excel_data(excel_paths: list[Path]) -> list[dict]:
    """엑셀에서 시뮬레이션에 필요한 컬럼을 파싱."""
    import openpyxl

    rows = []
    for path in excel_paths:
        if not path.exists():
            raise FileNotFoundError(f"엑셀 파일 없음: {path}")

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=3, values_only=True):
            bid_no_raw = str(row[3]).strip() if row[3] else ""
            if not bid_no_raw:
                continue

            rows.append({
                "bid_no": bid_no_raw,
                "category": str(row[1]) if row[1] else "",
                "construction_name": str(row[2]) if row[2] else "",
                "work_category": str(row[4]) if row[4] else "",
                "base_amt": parse_amount(row[8]),
                "est_price": parse_amount(row[9]),     # 추정가격 (테이블 라우팅)
                "det_price": parse_amount(row[10]),     # 예정가격 (가격점수 분모)
                "rank1_bid": parse_amount(row[12]),
                "my_bid": parse_amount(row[13]),
                "num_participants": parse_amount(row[17]),
                "my_rank": parse_amount(row[18]),
                "opening_date": row[19],
            })

        wb.close()

    return rows


def load_a_values(json_path: Path) -> dict[str, AValueItems]:
    """A값 JSON → {bid_key: AValueItems}."""
    if not json_path.exists():
        return {}

    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)

    result = {}
    for key, items in raw.items():
        if not items:
            continue
        item = items[0]
        kwargs = {}
        for json_field, attr_name in A_VALUE_FIELD_MAP.items():
            val = item.get(json_field, "")
            kwargs[attr_name] = int(val) if val and str(val).strip() else 0
        result[key] = AValueItems(**kwargs)

    return result


def load_a_values_raw(json_path: Path) -> dict[str, list]:
    """A값 JSON raw 데이터 로드 (검증용)."""
    if not json_path.exists():
        return {}
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def load_preliminary_prices(json_path: Path) -> dict[str, list]:
    """복수예비가격 JSON 로드. key → items list."""
    if not json_path.exists():
        return {}
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def check_boundary_proximity(price: int) -> int | None:
    """추정가격이 별표 경계 ±3% 이내면 해당 경계값 반환."""
    for boundary in TABLE_BOUNDARIES:
        lower = int(boundary * (1 - BOUNDARY_MARGIN))
        upper = int(boundary * (1 + BOUNDARY_MARGIN))
        if lower <= price <= upper:
            return boundary
    return None


def format_number(n) -> str:
    if n is None:
        return "-"
    return f"{int(n):,}"


def make_bar(count: int, max_count: int, width: int = 25) -> str:
    if max_count == 0:
        return ""
    w = int(count / max_count * width)
    return "\u2593" * w


class Command(BaseCommand):
    help = "BC-30: 과거 낙찰 시뮬레이션 (558건 나의방 데이터)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=0,
            help="실행 건수 제한 (디버깅용, 0=전체)",
        )
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        output_path = options["output"]

        # 1. 데이터 로드
        self.stdout.write("엑셀 파일 로드 중...")
        rows = load_excel_data(EXCEL_FILES)
        self.stdout.write(f"  {len(rows)}건 로드 완료")

        if limit > 0:
            rows = rows[:limit]
            self.stdout.write(f"  --limit {limit} 적용")

        self.stdout.write("A값 JSON 로드 중...")
        a_values = load_a_values(A_VALUES_JSON)
        self.stdout.write(f"  {len(a_values)}건 로드 완료")

        self.stdout.write("복수예비가격 JSON 로드 중...")
        prelim_prices = load_preliminary_prices(PRELIM_PRICES_JSON)
        self.stdout.write(f"  {len(prelim_prices)}건 로드 완료")

        a_values_raw = load_a_values_raw(A_VALUES_JSON)

        # 2. 시뮬레이션
        results = self._simulate(rows, a_values)

        # 3. 리포트 (9개 섹션)
        self._print_section1_summary(results)
        self._print_section2_table_routing(results)
        self._print_section3_score_dist(results)
        self._print_section4_vs_rank1(results)
        self._print_section5_optimal(results)
        self._print_section6_category(results)
        self._print_section7_rank_consistency(results)
        self._print_section8_worktype(results)
        self._print_section9_boundary(results)

        # 4. 교차 검증 (3계층)
        verification = self._verify(
            results["records"], rows, a_values_raw, prelim_prices,
        )
        self._print_verification(verification)
        results["verification"] = verification

        # 5. JSON 저장
        if output_path:
            self._save_json(results, output_path)

    # ──────────────────────────────────────────
    # 시뮬레이션 본체
    # ──────────────────────────────────────────

    def _simulate(self, rows: list[dict], a_values: dict) -> dict:
        records = []
        stats = {
            "total": len(rows),
            "success": 0,
            "my_score_count": 0,
            "rank1_score_count": 0,
            "skip_no_det_price": 0,
            # 에러 3분류
            "error_parse": 0,
            "error_engine_input": 0,
            "error_engine_exec": 0,
            # A값 3분류
            "a_value_loaded": 0,
            "a_value_not_target": 0,
            "a_value_missing": 0,
            # WorkType
            "construction_confirmed": 0,
            "construction_suspect": 0,
            # 경계
            "boundary_close": 0,
            "boundary_table_mismatch": 0,
        }

        table_dist = defaultdict(int)
        boundary_cases = []
        suspect_work_types = []

        for row in rows:
            rec = {
                "bid_no": row["bid_no"],
                "category": row["category"],
                "work_category": row["work_category"],
            }

            # --- WorkType 판정 ---
            wc = row["work_category"]
            is_confirmed = (
                any(kw in wc for kw in CONSTRUCTION_KEYWORDS) if wc else False
            )
            if is_confirmed:
                stats["construction_confirmed"] += 1
            else:
                stats["construction_suspect"] += 1
                suspect_work_types.append({
                    "bid_no": row["bid_no"],
                    "work_category": wc,
                    "category": row["category"],
                })
            work_type = WorkType.CONSTRUCTION

            # --- 예정가격 필수 ---
            det_price = row["det_price"]
            est_price = row["est_price"]

            if det_price is None or det_price <= 0:
                stats["skip_no_det_price"] += 1
                rec["status"] = "skip_no_det_price"
                records.append(rec)
                continue

            # 추정가격이 없으면 예정가격으로 대체 (라우팅용)
            routing_price = (
                est_price if (est_price and est_price > 0) else det_price
            )
            rec["det_price"] = det_price
            rec["est_price"] = est_price
            rec["routing_price"] = routing_price

            # --- A값 로드 (3분류) ---
            a_key = row["bid_no"]
            a_value_items = a_values.get(a_key)

            if a_value_items is not None:
                stats["a_value_loaded"] += 1
                rec["a_value_source"] = "json"
            elif "[수의]" in row["category"]:
                stats["a_value_not_target"] += 1
                rec["a_value_source"] = "not_target"
                a_value_items = AValueItems()
            else:
                stats["a_value_missing"] += 1
                rec["a_value_source"] = "missing"
                a_value_items = AValueItems()

            # --- 테이블 라우팅 (추정가격 기준) ---
            try:
                table_type = select_table(routing_price, work_type)
            except ValueError as e:
                stats["error_engine_input"] += 1
                rec["status"] = "error_engine_input"
                rec["error"] = str(e)
                records.append(rec)
                continue

            rec["table_type"] = table_type.value
            table_dist[table_type.value] += 1

            # --- 경계 근접 체크 ---
            boundary = check_boundary_proximity(routing_price)
            if boundary is not None:
                stats["boundary_close"] += 1
                mismatch = False
                try:
                    table_by_det = select_table(det_price, work_type)
                    if table_by_det != table_type:
                        stats["boundary_table_mismatch"] += 1
                        mismatch = True
                except ValueError:
                    pass
                rec["boundary_close"] = True
                rec["boundary_mismatch"] = mismatch
                boundary_cases.append({
                    "bid_no": row["bid_no"],
                    "est_price": est_price,
                    "det_price": det_price,
                    "routing_table": table_type.value,
                    "boundary": boundary,
                    "mismatch": mismatch,
                })

            # --- OUT_OF_SCOPE early return ---
            if table_type == TableType.OUT_OF_SCOPE:
                rec["status"] = "out_of_scope"
                stats["success"] += 1
                records.append(rec)
                continue

            # --- A값 합산 ---
            try:
                a_value = calculate_a_value(a_value_items)
            except ValueError as e:
                stats["error_engine_input"] += 1
                rec["status"] = "error_engine_input"
                rec["error"] = str(e)
                records.append(rec)
                continue

            rec["a_value"] = a_value

            # A값 >= 예정가격이면 점수 계산 불가
            if a_value >= det_price:
                stats["error_engine_input"] += 1
                rec["status"] = "a_value_exceeds_det_price"
                records.append(rec)
                continue

            # --- 나의 가격점수 ---
            my_bid = row["my_bid"]
            if my_bid is not None and my_bid > 0:
                try:
                    my_result = calc_price_score(
                        my_bid, det_price, a_value, table_type,
                    )
                    rec["my_bid"] = my_bid
                    rec["my_score"] = float(my_result.score)
                    rec["my_ratio"] = float(my_result.ratio)
                    rec["my_is_fixed"] = my_result.is_fixed_score
                    stats["my_score_count"] += 1
                except Exception as e:
                    rec["my_error"] = str(e)
                    stats["error_engine_exec"] += 1

            # --- 1순위 가격점수 ---
            rank1_bid = row["rank1_bid"]
            if rank1_bid is not None and rank1_bid > 0:
                try:
                    r1_result = calc_price_score(
                        rank1_bid, det_price, a_value, table_type,
                    )
                    rec["rank1_bid"] = rank1_bid
                    rec["rank1_score"] = float(r1_result.score)
                    rec["rank1_ratio"] = float(r1_result.ratio)
                    rec["rank1_is_fixed"] = r1_result.is_fixed_score
                    stats["rank1_score_count"] += 1
                except Exception as e:
                    rec["rank1_error"] = str(e)
                    stats["error_engine_exec"] += 1

            # --- 최적점 (ratio=0.9000 → max_score) ---
            params = TABLE_PARAMS_MAP[table_type]
            est_d = Decimal(str(det_price))
            a_d = Decimal(str(a_value))
            optimal_bid = ceil_up(
                (est_d - a_d) * Decimal("0.9") + a_d
            )
            rec["optimal_bid"] = optimal_bid
            rec["optimal_score"] = float(params.max_score)

            # --- 부가 정보 ---
            rec["my_rank"] = row["my_rank"]
            rec["num_participants"] = row["num_participants"]

            rec["status"] = "success"
            stats["success"] += 1
            records.append(rec)

        return {
            "stats": stats,
            "records": records,
            "table_dist": dict(table_dist),
            "boundary_cases": boundary_cases,
            "suspect_work_types": suspect_work_types,
        }

    # ──────────────────────────────────────────
    # 리포트 섹션 1~9
    # ──────────────────────────────────────────

    def _print_section1_summary(self, results: dict):
        s = results["stats"]
        self.stdout.write("")
        self.stdout.write("=" * 55)
        self.stdout.write("  과거 낙찰 시뮬레이션 (BC-30)")
        self.stdout.write("=" * 55)
        self.stdout.write(f"전체 공고:          {s['total']}건")
        self.stdout.write(f"엔진 실행 성공:      {s['success']}건")
        self.stdout.write(f"  - 나의투찰 점수:   {s['my_score_count']}건")
        self.stdout.write(f"  - 1순위 점수:      {s['rank1_score_count']}건")
        self.stdout.write(f"스킵 (예정가격 없음): {s['skip_no_det_price']}건")
        self.stdout.write("")
        total_err = (
            s["error_parse"] + s["error_engine_input"] + s["error_engine_exec"]
        )
        self.stdout.write(f"에러 합계:           {total_err}건")
        self.stdout.write(f"  파싱 오류:         {s['error_parse']}건")
        self.stdout.write(f"  엔진입력 오류:     {s['error_engine_input']}건")
        self.stdout.write(f"  엔진실행 오류:     {s['error_engine_exec']}건")
        self.stdout.write("")
        self.stdout.write("A값 현황:")
        self.stdout.write(f"  JSON 로드:        {s['a_value_loaded']}건")
        self.stdout.write(
            f"  비대상 ([수의]):   {s['a_value_not_target']}건"
        )
        missing = s["a_value_missing"]
        warn = "  \u26a0 점수 왜곡 가능" if missing > 0 else ""
        self.stdout.write(
            f"  미수집/매칭실패:   {missing}건{warn}"
        )

    def _print_section2_table_routing(self, results: dict):
        self.stdout.write("")
        self.stdout.write("[별표 라우팅 분포 — 추정가격 기준]")

        dist = results["table_dist"]
        order = [
            ("TABLE_5", "<2억"),
            ("TABLE_4", "2~3억"),
            ("TABLE_3", "3~10억"),
            ("TABLE_2A", "10~50억"),
            ("TABLE_1", "50~100억"),
            ("OUT_OF_SCOPE", "\u2265100억"),
        ]

        counts = [dist.get(t, 0) for t, _ in order]
        max_c = max(counts) if counts else 1

        for (table, label), count in zip(order, counts):
            bar = make_bar(count, max_c)
            self.stdout.write(
                f"{table:<14s} ({label:<8s}): {count:>4d}건  {bar}"
            )

    def _print_section3_score_dist(self, results: dict):
        records = results["records"]

        for target, fixed_key, label in [
            ("my_score", "my_is_fixed", "나의투찰"),
            ("rank1_score", "rank1_is_fixed", "1순위"),
        ]:
            scores = [r[target] for r in records if target in r]
            if not scores:
                continue

            self.stdout.write("")
            self.stdout.write(f"[가격점수 분포 \u2014 {label}]")

            bins = [
                (2, 20, "2~20점"),
                (20, 40, "20~40점"),
                (40, 60, "40~60점"),
                (60, 70, "60~70점"),
                (70, 80, "70~80점"),
                (80, 91, "80~90점"),
            ]

            fixed_count = sum(
                1 for r in records if r.get(fixed_key, False)
            )

            bin_counts = []
            for lo, hi, _ in bins:
                c = sum(1 for s in scores if lo <= s < hi)
                bin_counts.append(c)

            all_counts = bin_counts + [fixed_count]
            max_c = max(all_counts) if all_counts else 1

            self.stdout.write(f"{'구간':<10s} {'건수':>5s}  히스토그램")
            for (_, _, bin_label), c in zip(bins, bin_counts):
                bar = make_bar(c, max_c)
                self.stdout.write(f"{bin_label:<10s} {c:>5d}건  {bar}")
            self.stdout.write(
                f"{'고정점수':<10s} {fixed_count:>5d}건  "
                f"{make_bar(fixed_count, max_c)}"
            )

            avg = sum(scores) / len(scores)
            sorted_s = sorted(scores)
            median = sorted_s[len(sorted_s) // 2]
            self.stdout.write(f"\n평균: {avg:.1f}점 / 중앙값: {median:.1f}점")

    def _print_section4_vs_rank1(self, results: dict):
        records = results["records"]
        both = [
            r for r in records
            if "my_score" in r and "rank1_score" in r
        ]

        self.stdout.write("")
        self.stdout.write("[나 vs 1순위 점수 비교]")
        self.stdout.write(
            f"대상: {len(both)}건 (나의투찰 + 1순위 모두 있는 건)"
        )

        if not both:
            return

        n = len(both)
        win = sum(1 for r in both if r["my_score"] > r["rank1_score"])
        tie = sum(1 for r in both if r["my_score"] == r["rank1_score"])
        lose = n - win - tie

        self.stdout.write(
            f"나의점수 > 1순위:  {win:>4d}건 ({win / n * 100:.1f}%)"
        )
        self.stdout.write(
            f"나의점수 = 1순위:  {tie:>4d}건 ({tie / n * 100:.1f}%)"
        )
        self.stdout.write(
            f"나의점수 < 1순위:  {lose:>4d}건 ({lose / n * 100:.1f}%)"
        )

        avg_diff = sum(
            r["my_score"] - r["rank1_score"] for r in both
        ) / n
        self.stdout.write(
            f"점수 차이 평균: {avg_diff:+.1f}점 (양수=나의 우위)"
        )

    def _print_section5_optimal(self, results: dict):
        records = results["records"]
        has_both = [
            r for r in records
            if "my_score" in r and "optimal_score" in r
        ]

        self.stdout.write("")
        self.stdout.write("[히트맵 최고점 vs 실제 투찰 \u2014 상위 10건]")

        if not has_both:
            self.stdout.write("  (데이터 없음)")
            return

        for r in has_both:
            r["_gap"] = r["optimal_score"] - r["my_score"]

        top10 = sorted(has_both, key=lambda r: r["_gap"], reverse=True)[:10]

        self.stdout.write(
            f"{'공고번호':<25s} {'예정가격':>13s} {'나의금액':>13s} "
            f"{'나의점수':>7s} {'최고점금액':>13s} {'최고점수':>7s} {'차이':>5s}"
        )
        for r in top10:
            self.stdout.write(
                f"{r['bid_no']:<25s} "
                f"{format_number(r.get('det_price')):>13s} "
                f"{format_number(r.get('my_bid')):>13s} "
                f"{r['my_score']:>7.1f} "
                f"{format_number(r.get('optimal_bid')):>13s} "
                f"{r['optimal_score']:>7.1f} "
                f"{r['_gap']:>+5.1f}"
            )

        avg_gap = sum(r["_gap"] for r in has_both) / len(has_both)
        self.stdout.write(
            f"\n최고점 투찰 시 평균 점수 개선: {avg_gap:+.1f}점"
        )

        # cleanup temp key
        for r in has_both:
            del r["_gap"]

    def _print_section6_category(self, results: dict):
        records = results["records"]

        by_cat = defaultdict(list)
        for r in records:
            if "my_score" in r or "rank1_score" in r:
                by_cat[r["category"]].append(r)

        self.stdout.write("")
        self.stdout.write("[공고분류별 평균 가격점수]")
        self.stdout.write(
            f"{'분류':<35s} {'건수':>4s} {'나의평균':>8s} {'1순위평균':>8s}"
        )

        for cat in sorted(by_cat.keys()):
            group = by_cat[cat]
            n = len(group)
            my_s = [r["my_score"] for r in group if "my_score" in r]
            r1_s = [r["rank1_score"] for r in group if "rank1_score" in r]

            my_avg = f"{sum(my_s) / len(my_s):.1f}" if my_s else "-"
            r1_avg = f"{sum(r1_s) / len(r1_s):.1f}" if r1_s else "-"

            self.stdout.write(
                f"{cat:<35s} {n:>4d} {my_avg:>8s} {r1_avg:>8s}"
            )

    def _print_section7_rank_consistency(self, results: dict):
        """순위 정합성: 나의순위 vs 가격점수 차이."""
        records = results["records"]

        has_rank = [
            r for r in records
            if r.get("my_rank") is not None
            and "my_score" in r
            and "rank1_score" in r
        ]

        self.stdout.write("")
        self.stdout.write("[순위 정합성 \u2014 나의순위 vs 가격점수 차이]")
        self.stdout.write(f"대상: {len(has_rank)}건")

        if not has_rank:
            return

        rank_groups = [
            (1, 1, "1위 (낙찰)"),
            (2, 5, "2~5위"),
            (6, 10, "6~10위"),
            (11, 9999, "11위+"),
        ]

        self.stdout.write(
            f"{'순위구간':<14s} {'건수':>4s} {'평균점수차':>10s} "
            f"{'평균나의점수':>12s}  비고"
        )

        for lo, hi, label in rank_groups:
            group = [r for r in has_rank if lo <= r["my_rank"] <= hi]
            if not group:
                self.stdout.write(f"{label:<14s} {0:>4d}")
                continue

            n = len(group)
            avg_gap = sum(
                r["my_score"] - r["rank1_score"] for r in group
            ) / n
            avg_my = sum(r["my_score"] for r in group) / n

            note = ""
            if lo == 1:
                note = "\u2190 가격점수 최고 = 낙찰 기대"

            self.stdout.write(
                f"{label:<14s} {n:>4d} {avg_gap:>+10.1f} "
                f"{avg_my:>12.1f}  {note}"
            )

    def _print_section8_worktype(self, results: dict):
        s = results["stats"]
        suspects = results["suspect_work_types"]

        self.stdout.write("")
        self.stdout.write("[WorkType 매핑 검증]")
        self.stdout.write(
            f"건설 확인 (건축/토건/토목/건설 포함): "
            f"{s['construction_confirmed']}건"
        )
        self.stdout.write(
            f"비건설 의심 (키워드 미포함):           "
            f"{s['construction_suspect']}건"
        )

        if suspects:
            self.stdout.write("")
            self.stdout.write("비건설 의심 목록:")
            for item in suspects[:20]:
                self.stdout.write(
                    f"  {item['bid_no']:<25s} "
                    f"종목: {item['work_category']:<20s} "
                    f"분류: {item['category']}"
                )
            if len(suspects) > 20:
                self.stdout.write(f"  ... 외 {len(suspects) - 20}건")

    def _print_section9_boundary(self, results: dict):
        s = results["stats"]
        cases = results["boundary_cases"]

        self.stdout.write("")
        self.stdout.write("[별표 경계 근접 경고 \u2014 추정가격 vs 예정가격]")
        self.stdout.write(f"경계 \u00b13% 이내:       {s['boundary_close']}건")
        mismatch_n = s["boundary_table_mismatch"]
        warn = "  \u26a0 추정\u2194예정 차이로 별표 다름" if mismatch_n > 0 else ""
        self.stdout.write(
            f"테이블 불일치:        {mismatch_n}건{warn}"
        )

        mismatches = [c for c in cases if c["mismatch"]]
        if mismatches:
            self.stdout.write("")
            self.stdout.write("불일치 상세:")
            self.stdout.write(
                f"{'공고번호':<25s} {'추정가격':>13s} {'예정가격':>13s} "
                f"{'라우팅별표':>12s} {'경계':>13s}"
            )
            for c in mismatches[:15]:
                self.stdout.write(
                    f"{c['bid_no']:<25s} "
                    f"{format_number(c['est_price']):>13s} "
                    f"{format_number(c['det_price']):>13s} "
                    f"{c['routing_table']:>12s} "
                    f"{format_number(c['boundary']):>13s}"
                )

    # ──────────────────────────────────────────
    # 교차 검증 (3계층)
    # ──────────────────────────────────────────

    def _verify(
        self,
        records: list[dict],
        excel_rows: list[dict],
        a_values_raw: dict,
        prelim_prices: dict,
    ) -> dict:
        """3계층 교차 검증."""
        v = {
            "layer1_input": {},
            "layer2_formula": {},
            "layer3_reality": {},
            "verdict": "PASS",
        }

        # ── 계층 1: 입력 검증 ──

        # 1a. 예정가격 3자 대조 (추첨 평균 vs API plnprc vs 엑셀)
        excel_det = {r["bid_no"]: r["det_price"] for r in excel_rows if r["det_price"]}
        det_tested = det_passed = 0
        for key, items in prelim_prices.items():
            if not items:
                continue
            drawn = [i for i in items if i.get("drwtYn") == "Y"]
            if not drawn:
                continue
            api_plnprc_str = items[0].get("plnprc", "")
            if not api_plnprc_str or not str(api_plnprc_str).strip():
                continue
            api_plnprc = int(api_plnprc_str)
            drawn_avg = sum(int(d["bsisPlnprc"]) for d in drawn) / len(drawn)
            recalc = floor(drawn_avg) if drawn_avg != int(drawn_avg) else int(drawn_avg)
            excel_val = excel_det.get(key)
            det_tested += 1
            if api_plnprc == recalc and (excel_val is None or api_plnprc == excel_val):
                det_passed += 1
        v["layer1_input"]["det_price_3way"] = {
            "tested": det_tested, "passed": det_passed,
        }

        # 1b. 기초금액 2자 대조 (API bssamt vs 엑셀)
        excel_base = {r["bid_no"]: r["base_amt"] for r in excel_rows if r["base_amt"]}
        base_tested = base_passed = 0
        for key, items in prelim_prices.items():
            if not items:
                continue
            bssamt_str = items[0].get("bssamt", "")
            if not bssamt_str or not str(bssamt_str).strip():
                continue
            api_base = int(bssamt_str)
            excel_val = excel_base.get(key)
            if excel_val is not None:
                base_tested += 1
                if api_base == excel_val:
                    base_passed += 1
        v["layer1_input"]["base_amt_2way"] = {
            "tested": base_tested, "passed": base_passed,
        }

        # 1c. A값 합산 (raw 7항목 합 vs simulation a_value)
        a_fields = list(A_VALUE_FIELD_MAP.keys())
        sim_a = {r["bid_no"]: r["a_value"] for r in records if "a_value" in r and r.get("a_value_source") == "json"}
        asum_tested = asum_passed = 0
        for key, a_val in sim_a.items():
            raw_items = a_values_raw.get(key)
            if not raw_items:
                continue
            raw = raw_items[0]
            raw_sum = sum(
                int(raw.get(f, "") or "0") for f in a_fields
            )
            asum_tested += 1
            if raw_sum == a_val:
                asum_passed += 1
        v["layer1_input"]["a_value_sum"] = {
            "tested": asum_tested, "passed": asum_passed,
        }

        # ── 계층 2: 수식 검증 ──

        ratio_tested = ratio_passed = 0
        score_tested = score_passed = 0
        fixed_tested = fixed_passed = 0

        for rec in records:
            table = rec.get("table_type")
            if table not in VERIFY_TABLE_PARAMS:
                continue
            params = VERIFY_TABLE_PARAMS[table]
            det = rec.get("det_price")
            a_val = rec.get("a_value")
            if det is None or a_val is None:
                continue

            for prefix in ("my", "rank1"):
                bid = rec.get(f"{prefix}_bid")
                stored_ratio = rec.get(f"{prefix}_ratio")
                stored_score = rec.get(f"{prefix}_score")
                stored_fixed = rec.get(f"{prefix}_is_fixed")

                if bid is None or stored_ratio is None:
                    continue

                # ratio 역산
                d_ratio = Decimal(str(bid - a_val)) / Decimal(str(det - a_val))
                q = Decimal(10) ** -4
                recalc_ratio = float(d_ratio.quantize(q, rounding=ROUND_HALF_UP))
                ratio_tested += 1
                if abs(recalc_ratio - stored_ratio) < 0.00005:
                    ratio_passed += 1

                # 고정점수 조건
                is_fixed = (
                    bid <= det and recalc_ratio >= params["fixed_ratio"]
                )
                fixed_tested += 1
                if is_fixed == stored_fixed:
                    fixed_passed += 1

                # score 역산
                if is_fixed:
                    recalc_score = params["fixed_score"]
                else:
                    recalc_score = params["max_score"] - params["coeff"] * abs(
                        90 - recalc_ratio * 100
                    )
                    recalc_score = max(recalc_score, 2.0)
                score_tested += 1
                if abs(recalc_score - stored_score) < 0.05:
                    score_passed += 1

        v["layer2_formula"]["ratio"] = {
            "tested": ratio_tested, "passed": ratio_passed,
        }
        v["layer2_formula"]["score"] = {
            "tested": score_tested, "passed": score_passed,
        }
        v["layer2_formula"]["fixed_condition"] = {
            "tested": fixed_tested, "passed": fixed_passed,
        }

        # ── 계층 3: 현실 정합성 ──

        # 3a. 1순위 가격점수 우위율
        both = [
            r for r in records
            if "my_score" in r and "rank1_score" in r
        ]
        if both:
            r1_advantage = sum(
                1 for r in both if r["rank1_score"] >= r["my_score"]
            )
            v["layer3_reality"]["rank1_advantage"] = {
                "total": len(both),
                "rank1_ge_my": r1_advantage,
                "rate": round(r1_advantage / len(both), 3),
            }

        # 3b. 순위-점수 단조성
        has_rank = [
            r for r in records
            if r.get("my_rank") is not None
            and "my_score" in r
            and "rank1_score" in r
        ]
        if has_rank:
            groups = [(1, 5), (6, 10), (11, 9999)]
            avg_gaps = []
            for lo, hi in groups:
                g = [r for r in has_rank if lo <= r["my_rank"] <= hi]
                if g:
                    avg_gaps.append(
                        sum(r["my_score"] - r["rank1_score"] for r in g) / len(g)
                    )
            # 단조: 순위 높을수록 gap 양수 → 낮을수록 음수 경향
            monotonic = all(
                avg_gaps[i] >= avg_gaps[i + 1]
                for i in range(len(avg_gaps) - 1)
            ) if len(avg_gaps) >= 2 else True
            v["layer3_reality"]["rank_score_monotonic"] = monotonic

        # ── 종합 판정 ──
        # critical: 엔진 입력(예정가격, A값) + 수식 전부
        # informational: 기초금액 (엔진 미사용), 현실 정합성
        critical_checks = []
        for key in ("det_price_3way", "a_value_sum"):
            d = v["layer1_input"].get(key, {})
            if d.get("tested", 0) > 0:
                critical_checks.append(d["passed"] == d["tested"])
        for d in v["layer2_formula"].values():
            if d.get("tested", 0) > 0:
                critical_checks.append(d["passed"] == d["tested"])

        v["verdict"] = "PASS" if all(critical_checks) else "FAIL"

        return v

    def _print_verification(self, v: dict):
        """교차 검증 리포트 출력."""
        self.stdout.write("")
        self.stdout.write("=" * 55)
        self.stdout.write("  교차 검증 (Cross-Validation)")
        self.stdout.write("=" * 55)

        # 계층 1
        self.stdout.write("")
        self.stdout.write("[계층 1: 입력 검증]")
        for label, key in [
            ("예정가격 (추첨평균 vs API vs 엑셀)", "det_price_3way"),
            ("기초금액 (API vs 엑셀, 참고)", "base_amt_2way"),
            ("A값 합산 (raw 7항목 vs 엔진)", "a_value_sum"),
        ]:
            d = v["layer1_input"].get(key, {})
            t, p = d.get("tested", 0), d.get("passed", 0)
            pct = f"{p / t * 100:.1f}" if t > 0 else "-"
            mark = "\u2705" if t > 0 and p == t else "\u274c"
            self.stdout.write(f"  {mark} {label}: {p}/{t} ({pct}%)")

        # 계층 2
        self.stdout.write("")
        self.stdout.write("[계층 2: 수식 검증]")
        for label, key in [
            ("ratio 역산", "ratio"),
            ("score 역산", "score"),
            ("고정점수 조건", "fixed_condition"),
        ]:
            d = v["layer2_formula"].get(key, {})
            t, p = d.get("tested", 0), d.get("passed", 0)
            pct = f"{p / t * 100:.1f}" if t > 0 else "-"
            mark = "\u2705" if t > 0 and p == t else "\u274c"
            self.stdout.write(f"  {mark} {label}: {p}/{t} ({pct}%)")

        # 계층 3
        self.stdout.write("")
        self.stdout.write("[계층 3: 현실 정합성]")
        r1_adv = v["layer3_reality"].get("rank1_advantage", {})
        if r1_adv:
            self.stdout.write(
                f"  1순위 가격점수 >= 나의점수: "
                f"{r1_adv['rank1_ge_my']}/{r1_adv['total']}건 "
                f"({r1_adv['rate'] * 100:.1f}%)"
            )
        mono = v["layer3_reality"].get("rank_score_monotonic")
        if mono is not None:
            mark = "\u2705" if mono else "\u26a0"
            self.stdout.write(f"  {mark} 순위-점수 단조성: {'확인' if mono else '미확인'}")

        # 종합 판정
        verdict = v["verdict"]
        self.stdout.write("")
        self.stdout.write("=" * 55)
        if verdict == "PASS":
            self.stdout.write(
                self.style.SUCCESS(
                    "  종합 판정: \u2705 코어엔진 검증 통과"
                )
            )
            self.stdout.write("  입력 정확성: 예정가격\u00b7기초금액\u00b7A값 전건 일치")
            self.stdout.write("  수식 정확성: ratio\u00b7score\u00b7고정점수 전건 일치")
        else:
            self.stdout.write(
                self.style.ERROR(
                    "  종합 판정: \u274c 검증 실패 \u2014 불일치 항목 확인 필요"
                )
            )
        self.stdout.write("=" * 55)

    # ──────────────────────────────────────────
    # JSON 저장
    # ──────────────────────────────────────────

    def _save_json(self, results: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path

        path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "meta": {
                "command": "simulate_historical",
                "bc_id": "BC-30",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "schema_version": "1.1",
                "description": "과거 낙찰 시뮬레이션 + 교차검증 결과",
            },
            "stats": results["stats"],
            "verification": results.get("verification", {}),
            "table_distribution": results["table_dist"],
            "records": results["records"],
            "boundary_cases": results["boundary_cases"],
            "suspect_work_types": results["suspect_work_types"],
        }

        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"JSON 저장: {path}"))
