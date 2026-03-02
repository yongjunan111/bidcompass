"""BC-29: 사정률 검증 리포트.

558건 나의방 엑셀 데이터로 사정률 공식을 검증한다.
implied 하한율 = 1순위금액 × 100 / (기초금액 × 1순위사정률) 로 역산하고,
나의사정률과 비교하여 오차를 분석한다.

사용:
    python manage.py verify_assessment_rate
    python manage.py verify_assessment_rate --threshold 0.01
    python manage.py verify_assessment_rate --compare-db
    python manage.py verify_assessment_rate --output data/collected/assessment_report.json
"""

import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand

# 독립 상수 (collect_bid_data와 결합도 제거)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
EXCEL_FILES = [
    BASE_DIR / "docs" / "나의방_낙찰2026-02- 2025.xlsx",
    BASE_DIR / "docs" / "나의방_낙찰2026-02-05_1.xlsx",
]
OUTPUT_DIR = BASE_DIR / "data" / "collected"

# 2026.1.30 시행 기준일 (하한율 +2%p 상향)
REGULATION_DATE = datetime(2026, 1, 30)


def parse_amount(val):
    """콤마 문자열/float/int → int. None이면 None."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if isinstance(val, float) and val != val:  # NaN check
            return None
        return int(val)
    s = str(val).strip().replace(",", "")
    return int(s) if s else None


def load_excel_data(excel_paths: list[Path]) -> list[dict]:
    """엑셀에서 검증에 필요한 컬럼을 파싱하여 리스트로 반환."""
    import openpyxl

    rows = []
    for path in excel_paths:
        if not path.exists():
            raise FileNotFoundError(f"엑셀 파일 없음: {path}")

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=3, values_only=True):
            bid_category = str(row[1]) if row[1] else ""  # B열: 공고 분류
            bid_no_raw = str(row[3]).strip() if row[3] else ""  # D열: 공고번호
            base_amt = parse_amount(row[8])       # I열: 기초금액
            est_price = parse_amount(row[10])      # K열: 예정가격
            rank1_bid = parse_amount(row[12])      # M열: 1순위금액
            my_bid = parse_amount(row[13])          # N열: 나의투찰금액
            rank1_rate = row[14]                    # O열: 1순위사정률
            my_rate = row[15]                       # P열: 나의사정률
            opening_date = row[19]                  # T열: 개찰일

            if not bid_no_raw:
                continue

            # 1순위사정률 float → Decimal (None이면 None)
            rank1_rate_d = (
                Decimal(str(rank1_rate)) if rank1_rate is not None else None
            )
            my_rate_d = (
                Decimal(str(my_rate)) if my_rate is not None else None
            )

            rows.append({
                "bid_no": bid_no_raw,
                "category": bid_category,
                "base_amt": base_amt,
                "est_price": est_price,
                "rank1_bid": rank1_bid,
                "my_bid": my_bid,
                "rank1_rate": rank1_rate_d,
                "my_rate": my_rate_d,
                "opening_date": opening_date,
            })

        wb.close()

    return rows


def calc_implied_floor(rank1_bid: int, base_amt: int, rank1_rate: Decimal) -> Decimal:
    """implied 하한율 역산. 곱셈 먼저, 나눗셈 1회 (정밀도 최적화)."""
    return (Decimal(str(rank1_bid)) * Decimal("100")) / (
        Decimal(str(base_amt)) * rank1_rate
    )


def calc_assessment_rate(
    bid_amount: int, base_amt: int, floor_rate: Decimal,
) -> Decimal:
    """사정률 계산. 곱셈 먼저, 나눗셈 1회."""
    return (Decimal(str(bid_amount)) * Decimal("100")) / (
        Decimal(str(base_amt)) * floor_rate
    )


def format_number(n) -> str:
    """숫자를 콤마 포함 문자열로."""
    if n is None:
        return "-"
    return f"{int(n):,}"


def make_histogram_bar(count: int, max_count: int, max_width: int = 30) -> str:
    """히스토그램 막대."""
    if max_count == 0:
        return ""
    width = int(count / max_count * max_width)
    return "\u2593" * width


class Command(BaseCommand):
    help = "BC-29: 사정률 검증 리포트 (558건 나의방 데이터 기반)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--threshold", type=float, default=0.05,
            help="일치 판정 임계값 (%%, 기본 0.05)",
        )
        parser.add_argument(
            "--compare-db", action="store_true",
            help="DB 낙찰하한율(success_lowest_rate)과 비교",
        )
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로 (예: data/collected/assessment_report.json)",
        )

    def handle(self, *args, **options):
        threshold = Decimal(str(options["threshold"]))
        compare_db = options["compare_db"]
        output_path = options["output"]

        # 1. 엑셀 로드
        self.stdout.write("엑셀 파일 로드 중...")
        rows = load_excel_data(EXCEL_FILES)
        self.stdout.write(f"  {len(rows)}건 로드 완료")

        # 2. 분석
        results = self._analyze(rows, threshold)

        # 3. 리포트 출력
        self._print_summary(results, threshold)
        self._print_distribution(results)
        self._print_category_analysis(results, threshold)
        self._print_regulation_analysis(results, threshold)

        if compare_db:
            self._print_db_comparison(results)

        self._print_sanity_check(results)
        self._print_top_mismatches(results)

        # 4. JSON 저장
        if output_path:
            self._save_json(results, output_path, threshold)

    def _analyze(self, rows: list[dict], threshold: Decimal) -> dict:
        """전체 분석 수행."""
        total = len(rows)
        has_my_bid = []
        has_rank1 = []
        verifiable = []  # 나의투찰 + 1순위 모두 있는 건
        rank1_only = []  # 1순위 데이터만 있는 건 (sanity check용)

        for row in rows:
            base = row["base_amt"]
            r1_bid = row["rank1_bid"]
            r1_rate = row["rank1_rate"]
            my_bid = row["my_bid"]
            my_rate = row["my_rate"]

            if my_bid is not None and my_rate is not None:
                has_my_bid.append(row)

            if (
                base is not None
                and r1_bid is not None
                and r1_rate is not None
                and base > 0
                and r1_rate > 0
            ):
                # implied 하한율 계산
                implied = calc_implied_floor(r1_bid, base, r1_rate)
                row["implied_floor"] = implied

                # 1순위 자체 검증 (sanity check)
                r1_recalc = calc_assessment_rate(r1_bid, base, implied)
                row["rank1_recalc"] = r1_recalc
                row["rank1_diff"] = abs(r1_recalc - r1_rate)
                rank1_only.append(row)
                has_rank1.append(row)

                # 나의사정률 검증
                if my_bid is not None and my_rate is not None:
                    my_recalc = calc_assessment_rate(my_bid, base, implied)
                    row["my_recalc"] = my_recalc
                    row["my_diff"] = abs(my_recalc - my_rate)
                    verifiable.append(row)

        # MAE 계산
        if verifiable:
            mae = sum(r["my_diff"] for r in verifiable) / len(verifiable)
        else:
            mae = Decimal("0")

        # 일치/불일치 분류
        match_tight = [r for r in verifiable if r["my_diff"] <= Decimal("0.01")]
        match_normal = [r for r in verifiable if r["my_diff"] <= threshold]
        mismatch = [r for r in verifiable if r["my_diff"] > threshold]

        return {
            "total": total,
            "has_my_bid": len(has_my_bid),
            "has_rank1": len(has_rank1),
            "verifiable": len(verifiable),
            "match_tight": len(match_tight),
            "match_normal": len(match_normal),
            "mismatch": len(mismatch),
            "mae": mae,
            "rows": rows,
            "verifiable_rows": verifiable,
            "rank1_rows": rank1_only,
        }

    def _print_summary(self, results: dict, threshold: Decimal):
        """섹션 1: 전체 요약."""
        v = results["verifiable"]
        self.stdout.write("")
        self.stdout.write("=" * 55)
        self.stdout.write("  사정률 검증 리포트 (BC-29)")
        self.stdout.write("=" * 55)
        self.stdout.write(f"전체 공고:          {results['total']}건")
        self.stdout.write(f"투찰 건:            {results['has_my_bid']}건 (나의투찰금액+사정률 있음)")
        self.stdout.write(f"1순위 데이터 있음:    {results['has_rank1']}건")
        self.stdout.write(f"검증 대상:          {v}건")
        self.stdout.write("")
        self.stdout.write("implied 하한율 기준:")

        pct_tight = (
            f"{results['match_tight'] / v * 100:.1f}" if v else "0.0"
        )
        pct_normal = (
            f"{results['match_normal'] / v * 100:.1f}" if v else "0.0"
        )
        pct_mismatch = (
            f"{results['mismatch'] / v * 100:.1f}" if v else "0.0"
        )

        self.stdout.write(
            f"  일치 (<=0.01%):   {results['match_tight']}건 ({pct_tight}%)"
        )
        self.stdout.write(
            f"  일치 (<={threshold}%):   {results['match_normal']}건 ({pct_normal}%)"
        )
        self.stdout.write(
            f"  불일치 (>{threshold}%):  {results['mismatch']}건 ({pct_mismatch}%)"
        )
        self.stdout.write(f"  MAE:             {float(results['mae']):.6f}")

    def _print_distribution(self, results: dict):
        """섹션 2: 오차 분포."""
        self.stdout.write("")
        self.stdout.write("[오차 분포]")

        bins = [
            (Decimal("0.000"), Decimal("0.001")),
            (Decimal("0.001"), Decimal("0.005")),
            (Decimal("0.005"), Decimal("0.010")),
            (Decimal("0.010"), Decimal("0.050")),
            (Decimal("0.050"), Decimal("0.100")),
            (Decimal("0.100"), Decimal("999")),
        ]
        labels = [
            "0.000 ~ 0.001",
            "0.001 ~ 0.005",
            "0.005 ~ 0.010",
            "0.010 ~ 0.050",
            "0.050 ~ 0.100",
            "0.100 ~      ",
        ]

        counts = []
        for lo, hi in bins:
            c = sum(
                1 for r in results["verifiable_rows"]
                if lo <= r["my_diff"] < hi
            )
            counts.append(c)

        max_count = max(counts) if counts else 1

        for label, count in zip(labels, counts):
            bar = make_histogram_bar(count, max_count)
            self.stdout.write(f"{label}  {bar:30s}  {count}건")

    def _print_category_analysis(self, results: dict, threshold: Decimal):
        """섹션 3: 공고 분류별 분석."""
        self.stdout.write("")
        self.stdout.write("[공고 분류별 분석]")

        # 분류별 그룹핑
        by_cat = defaultdict(list)
        for r in results["verifiable_rows"]:
            by_cat[r["category"]].append(r)

        self.stdout.write(
            f"{'분류':<35s} {'건수':>4s}  {'MAE':>8s}  {'일치율':>6s}"
        )

        for cat in sorted(by_cat.keys()):
            rows = by_cat[cat]
            n = len(rows)
            mae = sum(r["my_diff"] for r in rows) / n
            match = sum(1 for r in rows if r["my_diff"] <= threshold)
            pct = match / n * 100
            self.stdout.write(
                f"{cat:<35s} {n:>4d}  {float(mae):>8.4f}  {pct:>5.1f}%"
            )

    def _print_regulation_analysis(self, results: dict, threshold: Decimal):
        """섹션 3b: 시행일 기준 분석 (2026.1.30 하한율 +2%p 시행)."""
        self.stdout.write("")
        self.stdout.write("[시행일 기준 분석 -- 2026.1.30 하한율 +2%p 시행]")

        before = []
        after = []
        unknown = []

        for r in results["verifiable_rows"]:
            od = r["opening_date"]
            if od is None:
                unknown.append(r)
            elif isinstance(od, datetime):
                if od < REGULATION_DATE:
                    before.append(r)
                else:
                    after.append(r)
            else:
                unknown.append(r)

        self.stdout.write(
            f"{'구간':<22s} {'건수':>4s}  {'MAE':>8s}  {'일치율':>6s}  비고"
        )

        for label, group, note in [
            ("2026.1.30 이전", before, "구 하한율 적용"),
            ("2026.1.30 이후", after, "신 하한율 적용"),
        ]:
            if group:
                n = len(group)
                mae = sum(r["my_diff"] for r in group) / n
                match = sum(1 for r in group if r["my_diff"] <= threshold)
                pct = match / n * 100
                self.stdout.write(
                    f"{label:<22s} {n:>4d}  {float(mae):>8.4f}  {pct:>5.1f}%  {note}"
                )
            else:
                self.stdout.write(f"{label:<22s}    0         -       -  {note}")

        if unknown:
            self.stdout.write(f"{'개찰일 없음':<22s} {len(unknown):>4d}")

    def _print_db_comparison(self, results: dict):
        """섹션 4: API 하한율 vs implied 하한율."""
        self.stdout.write("")
        self.stdout.write("[API 하한율 vs implied 하한율]")

        try:
            from g2b.models import BidAnnouncement
            # DB 연결 테스트
            BidAnnouncement.objects.exists()
        except Exception as e:
            self.stderr.write(
                self.style.WARNING(f"  DB 연결 실패 — --compare-db 건너뜀: {e}")
            )
            return

        compared = []
        db_errors = 0
        for r in results["rank1_rows"]:
            bid_no_raw = r["bid_no"]
            # 공고번호-차수 분리
            parts = bid_no_raw.rsplit("-", 1)
            if len(parts) == 2 and 1 <= len(parts[1]) <= 3 and parts[1].isdigit():
                ntce_no, ntce_ord = parts
            else:
                ntce_no, ntce_ord = bid_no_raw, ""

            try:
                ann = BidAnnouncement.objects.get(
                    bid_ntce_no=ntce_no, bid_ntce_ord=ntce_ord,
                )
            except BidAnnouncement.DoesNotExist:
                # ord fallback
                if not ntce_ord:
                    try:
                        ann = BidAnnouncement.objects.get(
                            bid_ntce_no=ntce_no, bid_ntce_ord="000",
                        )
                    except BidAnnouncement.DoesNotExist:
                        continue
                else:
                    continue
            except Exception:
                db_errors += 1
                continue

            if ann.success_lowest_rate is None:
                continue

            api_floor = ann.success_lowest_rate / Decimal("100")
            implied = r["implied_floor"]
            floor_diff = abs(api_floor - implied)

            compared.append({
                "bid_no": bid_no_raw,
                "api_floor": api_floor,
                "implied_floor": implied,
                "floor_diff": floor_diff,
                "category": r["category"],
            })

        n = len(compared)
        self.stdout.write(f"DB 매칭 건:        {n}건")
        if db_errors:
            self.stderr.write(
                self.style.WARNING(f"  DB 쿼리 오류:    {db_errors}건 (건너뜀)")
            )

        if not compared:
            self.stdout.write("  (매칭 데이터 없음)")
            return

        exact = sum(1 for c in compared if c["floor_diff"] <= Decimal("0.0001"))
        close = sum(1 for c in compared if c["floor_diff"] <= Decimal("0.01"))
        far = sum(1 for c in compared if c["floor_diff"] > Decimal("0.01"))

        self.stdout.write(f"완전 일치 (<=0.0001): {exact}건 ({exact / n * 100:.1f}%)")
        self.stdout.write(f"차이 <=0.01:        {close}건 ({close / n * 100:.1f}%)")
        self.stdout.write(f"차이 >0.01:         {far}건 ({far / n * 100:.1f}%)")

        # 차이 큰 상위 10건
        compared.sort(key=lambda c: c["floor_diff"], reverse=True)
        top10 = compared[:10]

        if top10:
            self.stdout.write("")
            self.stdout.write("[API!=implied 상위 10건]")
            self.stdout.write(
                f"{'공고번호':<25s} {'API하한율':>10s} {'implied':>10s} "
                f"{'차이':>8s}  공고분류"
            )
            for c in top10:
                self.stdout.write(
                    f"{c['bid_no']:<25s} "
                    f"{float(c['api_floor']):>10.5f} "
                    f"{float(c['implied_floor']):>10.5f} "
                    f"{float(c['floor_diff']):>8.5f}  "
                    f"{c['category']}"
                )

    def _print_sanity_check(self, results: dict):
        """섹션 5: 1순위 자체검증."""
        self.stdout.write("")
        self.stdout.write("[1순위 자체검증 -- implied 하한율 -> 1순위사정률 역산]")

        rank1_rows = results["rank1_rows"]
        n = len(rank1_rows)
        self.stdout.write(f"대상: {results['total']}건 중 1순위 데이터 있는 {n}건")

        if n == 0:
            self.stdout.write("  (데이터 없음)")
            return

        mae = sum(r["rank1_diff"] for r in rank1_rows) / n
        errors = sum(1 for r in rank1_rows if r["rank1_diff"] > Decimal("0.001"))

        self.stdout.write(f"MAE: {float(mae):.6f} (정의상 완벽)")
        self.stdout.write(f"오차 >0.001:  {errors}건")
        self.stdout.write("")
        self.stdout.write(
            "* implied가 1순위에서 역산한 값이므로 MAE=0이 당연."
        )
        self.stdout.write(
            "  이 검증의 목적: 파싱 오류/타입 변환 오류 조기 발견."
        )
        self.stdout.write(
            "  여기서 1건이라도 틀리면 엑셀 파싱 버그."
        )

    def _print_top_mismatches(self, results: dict):
        """섹션 6: 나의사정률 불일치 TOP 10."""
        self.stdout.write("")
        self.stdout.write("[나의사정률 불일치 TOP 10]")

        verifiable = results["verifiable_rows"]
        if not verifiable:
            self.stdout.write("  (검증 대상 없음)")
            return

        sorted_rows = sorted(verifiable, key=lambda r: r["my_diff"], reverse=True)
        top10 = sorted_rows[:10]

        self.stdout.write(
            f"{'공고번호':<25s} {'기초금액':>15s} {'나의금액':>15s} "
            f"{'implied':>8s} {'엑셀률':>8s} {'역산률':>8s} {'오차':>8s}"
        )
        for r in top10:
            self.stdout.write(
                f"{r['bid_no']:<25s} "
                f"{format_number(r['base_amt']):>15s} "
                f"{format_number(r['my_bid']):>15s} "
                f"{float(r['implied_floor']):>8.4f} "
                f"{float(r['my_rate']):>8.4f} "
                f"{float(r['my_recalc']):>8.4f} "
                f"{float(r['my_diff']):>8.4f}"
            )

    def _save_json(self, results: dict, output_path: str, threshold: Decimal):
        """JSON 결과 저장."""
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path

        path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "threshold": float(threshold),
            "summary": {
                "total": results["total"],
                "has_my_bid": results["has_my_bid"],
                "has_rank1": results["has_rank1"],
                "verifiable": results["verifiable"],
                "match_tight_0_01": results["match_tight"],
                "match_normal": results["match_normal"],
                "mismatch": results["mismatch"],
                "mae": float(results["mae"]),
            },
            "details": [
                {
                    "bid_no": r["bid_no"],
                    "category": r["category"],
                    "base_amt": r["base_amt"],
                    "my_bid": r["my_bid"],
                    "implied_floor": float(r["implied_floor"]),
                    "my_rate_excel": float(r["my_rate"]),
                    "my_rate_calc": float(r["my_recalc"]),
                    "diff": float(r["my_diff"]),
                }
                for r in sorted(
                    results["verifiable_rows"],
                    key=lambda r: r["my_diff"],
                    reverse=True,
                )
            ],
        }

        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"JSON 저장: {path}"))
