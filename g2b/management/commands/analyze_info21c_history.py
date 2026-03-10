"""인포21C 투찰성향 5년 EDA (2021~2026, 2,983건).

부모님 회사가 인포21C 추천을 따라 투찰한 5년치 실적 분석.
BidCompass 엔진 우위 정량 입증 + TABLE별 튜닝 방향 도출.

산출물: JSON 1개 + 차트 7개 (matplotlib)

사용:
    python manage.py analyze_info21c_history                # 전체
    python manage.py analyze_info21c_history --task 0       # 품질만
    python manage.py analyze_info21c_history --task 1,6     # 정확도+포텐셜
    python manage.py analyze_info21c_history --no-charts    # 차트 생략
"""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UNIT_EOUK = 1_0000_0000

# TABLE 경계 (bid_engine.py:select_table, CONSTRUCTION 가정)
TABLE_BOUNDARIES = [
    ("TABLE_5", 0, 2 * UNIT_EOUK),
    ("TABLE_4", 2 * UNIT_EOUK, 3 * UNIT_EOUK),
    ("TABLE_3", 3 * UNIT_EOUK, 10 * UNIT_EOUK),
    ("TABLE_2A", 10 * UNIT_EOUK, 50 * UNIT_EOUK),
    ("TABLE_1", 50 * UNIT_EOUK, 100 * UNIT_EOUK),
]

# 금액대 세그먼트
AMT_SEGMENTS = [
    ("<3억", 0, 3 * UNIT_EOUK),
    ("3~5억", 3 * UNIT_EOUK, 5 * UNIT_EOUK),
    ("5~10억", 5 * UNIT_EOUK, 10 * UNIT_EOUK),
    ("10~30억", 10 * UNIT_EOUK, 30 * UNIT_EOUK),
    ("30~50억", 30 * UNIT_EOUK, 50 * UNIT_EOUK),
    ("50+억", 50 * UNIT_EOUK, 100 * UNIT_EOUK),
]

# 제도 변경일 (2026.1.30 시행)
REGIME_CUTOFF = datetime(2026, 1, 30)

ALL_TASKS = list(range(8))


def _clean(obj):
    """Recursively clean floats (NaN->None, round to 6 decimals)."""
    if isinstance(obj, float):
        if obj != obj:  # NaN
            return None
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


def _classify_table(base_amt: int) -> str:
    """예비기초금액 기준 TABLE 분류 (CONSTRUCTION 가정)."""
    for name, lo, hi in TABLE_BOUNDARIES:
        if lo <= base_amt < hi:
            return name
    return "OUT_OF_SCOPE"


def _classify_amt_seg(base_amt: int) -> str:
    for name, lo, hi in AMT_SEGMENTS:
        if lo <= base_amt < hi:
            return name
    return "50+억"


def _parse_money(val) -> int | None:
    """금액 문자열 -> int. None/''/숫자 처리."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).replace(",", "").strip()
    if not s or s == "-":
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_rate(val) -> float | None:
    """사정율 문자열 -> float. '99.9492 (-0.0507)' 형태 처리."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s == "-":
        return None
    # '99.9492 (-0.0507)' -> '99.9492'
    s = s.split("(")[0].strip()
    try:
        return float(s)
    except ValueError:
        return None


def _parse_date(val) -> datetime | None:
    """개찰일 파싱. '21-01-05 13:00' 형태."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    s = str(val).strip()
    for fmt in ("%y-%m-%d %H:%M", "%y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _percentile(values: list[float], p: float) -> float:
    """Simple percentile (0~100)."""
    if not values:
        return 0.0
    s = sorted(values)
    k = (p / 100) * (len(s) - 1)
    f = int(k)
    c = f + 1
    if c >= len(s):
        return s[-1]
    d = k - f
    return s[f] + d * (s[c] - s[f])


def _safe_mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _safe_stdev(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) >= 2 else 0.0


def _safe_median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


class Command(BaseCommand):
    help = "인포21C 투찰성향 5년 EDA (2021~2026)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--task", type=str, default="",
            help="특정 태스크만 실행 (0~7 콤마구분, 미지정시 전체)",
        )
        parser.add_argument(
            "--no-charts", action="store_true",
            help="차트 생성 생략",
        )
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로",
        )

    def handle(self, *args, **options):
        if options["task"]:
            tasks = [int(t.strip()) for t in options["task"].split(",")]
        else:
            tasks = ALL_TASKS

        self.no_charts = options["no_charts"]
        output_path = (
            options["output"]
            or "data/collected/info21c_history_eda.json"
        )

        self.stdout.write("=" * 70)
        self.stdout.write("  인포21C 투찰성향 5년 EDA (2021~2026)")
        self.stdout.write("=" * 70)
        self.stdout.write(f"  태스크: {tasks}")
        self.stdout.write("")

        # Load data
        self.stdout.write("[Loading] xlsx 파일 로딩 중...")
        self.rows = self._load_xlsx_files()
        self.stdout.write(f"  전체 로딩: {len(self.rows):,}건")

        # Filter
        invalid_rows = [r for r in self.rows if r["base_amt"] is None]
        over_100 = [r for r in self.rows
                     if r["base_amt"] is not None
                     and r["base_amt"] >= 100 * UNIT_EOUK]
        self.data = [r for r in self.rows
                     if r["base_amt"] is not None
                     and r["base_amt"] < 100 * UNIT_EOUK]
        self.exclusion = {
            "total_loaded": len(self.rows),
            "base_amt_null": len(invalid_rows),
            "over_100b": len(over_100),
            "final_count": len(self.data),
        }

        # Floor classification
        unknown_floor = [r for r in self.data
                         if r["floor_diff"] is None]
        self.floor_known = [r for r in self.data
                            if r["floor_diff"] is not None]
        self.passed = [r for r in self.floor_known if r["floor_diff"] >= 0]
        self.failed = [r for r in self.floor_known if r["floor_diff"] < 0]
        self.exclusion["floor_null"] = len(unknown_floor)
        self.exclusion["floor_known"] = len(self.floor_known)

        self.stdout.write(
            f"  필터 후: {len(self.data):,}건 "
            f"(base_amt null {len(invalid_rows)}, "
            f"100억+ {len(over_100)}, "
            f"floor null {len(unknown_floor)})"
        )

        results: dict[str, Any] = {"exclusion_summary": self.exclusion}

        dispatch = {
            0: ("데이터 품질", self._task0_quality),
            1: ("인포21C 정확도 감사", self._task1_accuracy),
            2: ("TABLE별 심층 분석", self._task2_table_deep),
            3: ("시계열 + 제도 변경", self._task3_timeseries),
            4: ("경쟁업체 프로파일링", self._task4_competitors),
            5: ("금액대 + 발주처 세분화", self._task5_segmentation),
            6: ("개선 포텐셜 정량화", self._task6_potential),
            7: ("종합 요약", self._task7_summary),
        }

        for t in tasks:
            if t not in dispatch:
                self.stderr.write(f"  알 수 없는 태스크: {t}")
                continue
            name, func = dispatch[t]
            self.stdout.write(f"\n{'─' * 60}")
            self.stdout.write(f"  [Task {t}] {name}")
            self.stdout.write(f"{'─' * 60}")
            try:
                results[f"task{t}"] = func()
            except Exception as e:
                self.stderr.write(f"  ✗ Task {t} 실패: {e}")
                results[f"task{t}"] = {"error": str(e)}

        self._save_json(results, output_path)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("  인포21C EDA 완료"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

    # ──────────────────────────────────────────────
    # Data loading
    # ──────────────────────────────────────────────

    def _load_xlsx_files(self) -> list[dict]:
        """6개 xlsx -> list[dict]."""
        import openpyxl

        docs_dir = BASE_DIR / "docs"
        files = sorted(docs_dir.glob("인포투찰성향_*.xlsx"))
        if not files:
            raise FileNotFoundError(
                f"인포투찰성향 xlsx 파일을 찾을 수 없습니다: {docs_dir}"
            )

        all_rows = []
        for fp in files:
            wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
            ws = wb.active
            headers = None
            for row in ws.iter_rows(values_only=True):
                if headers is None:
                    headers = list(row)
                    continue
                raw = dict(zip(headers, row))
                parsed = self._parse_row(raw)
                if parsed:
                    all_rows.append(parsed)
            wb.close()
            self.stdout.write(f"  {fp.name}: {len(all_rows):,}건 (누적)")

        return all_rows

    def _parse_row(self, raw: dict) -> dict | None:
        """원본 row -> 분석용 dict."""
        base_amt = _parse_money(raw.get("예비기초금액"))
        est_price = _parse_money(raw.get("예정가격"))
        a_value = _parse_money(raw.get("A값"))
        net_cost = _parse_money(raw.get("순공사원가"))
        our_bid = _parse_money(raw.get("(자사) 입찰금액"))
        rank1_amt = _parse_money(raw.get("1순위금액"))
        floor_price = _parse_money(raw.get("낙찰하한가"))
        floor_diff = _parse_money(raw.get("낙찰하한금액차"))
        rank1_diff = _parse_money(raw.get("1순위금액차"))

        owner_rate = _parse_rate(raw.get("발주처사정율"))
        our_rate = _parse_rate(raw.get("(자사) 사정율"))
        rate_dev = raw.get("사정율편차")
        if isinstance(rate_dev, str):
            try:
                rate_dev = float(rate_dev)
            except ValueError:
                rate_dev = None

        bid_rate_str = raw.get("투찰율")
        bid_rate = None
        if bid_rate_str is not None:
            try:
                bid_rate = float(bid_rate_str)
            except (ValueError, TypeError):
                pass

        our_bid_over_base = _parse_rate(raw.get("(자사) 입찰가/기초가"))
        rank1_rate = _parse_rate(raw.get("1순위 사정율"))

        dt = _parse_date(raw.get("개찰일"))

        our_rank = raw.get("자사순위")
        if isinstance(our_rank, str):
            try:
                our_rank = int(our_rank)
            except ValueError:
                our_rank = None

        # Derived fields
        table_type = None
        amt_seg = None
        if base_amt is not None:
            if base_amt >= 100 * UNIT_EOUK:
                table_type = "OUT_OF_SCOPE"
            else:
                table_type = _classify_table(base_amt)
            amt_seg = _classify_amt_seg(base_amt)

        year = dt.year if dt else None
        quarter = f"{dt.year}Q{(dt.month - 1) // 3 + 1}" if dt else None
        regime = None
        if dt:
            regime = "post" if dt >= REGIME_CUTOFF else "pre"

        return {
            "ntce_no": raw.get("입찰공고번호"),
            "title": raw.get("공고명"),
            "org": raw.get("발주처"),
            "sector": raw.get("업종"),
            "open_dt": dt,
            "base_amt": base_amt,
            "a_value": a_value,
            "est_price": est_price,
            "net_cost": net_cost,
            "bid_rate": bid_rate,  # 투찰하한율 (인포21C 표기상 '투찰율')
            "owner_rate": owner_rate,
            "our_rate": our_rate,
            "rate_dev": rate_dev,
            "our_bid_over_base": our_bid_over_base,
            "our_bid": our_bid,
            "rank1_amt": rank1_amt,
            "rank1_diff": rank1_diff,
            "floor_price": floor_price,
            "floor_diff": floor_diff,
            "our_rank": our_rank,
            "rank1_company": raw.get("1순위업체"),
            "rank1_bizno": raw.get("1순위업체 사업자번호"),
            "rank1_rate": rank1_rate,
            # derived
            "table_type": table_type,
            "amt_seg": amt_seg,
            "year": year,
            "quarter": quarter,
            "regime": regime,
            "passed_floor": floor_diff >= 0 if floor_diff is not None else None,
        }

    # ──────────────────────────────────────────────
    # Task 0: 데이터 품질
    # ──────────────────────────────────────────────

    def _task0_quality(self) -> dict:
        data = self.data
        result = {}

        # 연도별 건수
        year_counts = Counter(r["year"] for r in data)
        result["by_year"] = dict(sorted(year_counts.items()))
        self.stdout.write("  연도별 건수:")
        for y, c in sorted(year_counts.items()):
            self.stdout.write(f"    {y}: {c:,}건")

        # TABLE별 분포
        table_counts = Counter(r["table_type"] for r in data)
        result["by_table"] = dict(sorted(table_counts.items()))
        self.stdout.write("  TABLE별 분포:")
        for t, c in sorted(table_counts.items()):
            self.stdout.write(f"    {t}: {c:,}건 ({c/len(data)*100:.1f}%)")

        # NULL 비율
        fields = [
            "base_amt", "est_price", "a_value", "owner_rate",
            "our_rate", "rank1_rate", "floor_diff", "our_rank",
        ]
        null_info = {}
        for f in fields:
            null_count = sum(1 for r in data if r[f] is None)
            null_info[f] = {
                "null": null_count,
                "pct": round(null_count / len(data) * 100, 2),
            }
        result["null_rates"] = null_info
        self.stdout.write("  NULL 비율:")
        for f, info in null_info.items():
            if info["null"] > 0:
                self.stdout.write(
                    f"    {f}: {info['null']}건 ({info['pct']}%)"
                )

        # 제외 건수
        result["exclusion_summary"] = self.exclusion
        self.stdout.write(f"  제외: base_amt null {self.exclusion['base_amt_null']}건, "
                          f"100억+ {self.exclusion['over_100b']}건")
        self.stdout.write(f"  floor null: {self.exclusion['floor_null']}건 "
                          f"(pass/fail 분석 제외)")
        self.stdout.write(
            f"  최종 분석 대상: {self.exclusion['final_count']:,}건"
        )

        # 이상치
        outliers = {}
        rates = [r["our_rate"] for r in data if r["our_rate"] is not None]
        if rates:
            extreme = [r for r in data
                       if r["our_rate"] is not None
                       and abs(r["our_rate"] - 100) > 5]
            outliers["our_rate_extreme"] = len(extreme)
        result["outliers"] = outliers

        return result

    # ──────────────────────────────────────────────
    # Task 1: 인포21C 정확도 감사
    # ──────────────────────────────────────────────

    def _task1_accuracy(self) -> dict:
        data = self.data
        result = {}

        # 편차 = 자사사정율 - 발주처사정율 (rate_dev)
        devs = [r["rate_dev"] for r in data if r["rate_dev"] is not None]
        abs_devs = [abs(d) for d in devs]

        if not devs:
            self.stdout.write("  사정율편차 데이터 없음")
            return {"error": "no deviation data"}

        mad = _safe_mean(abs_devs)
        signed_mean = _safe_mean(devs)
        p50 = _safe_median(abs_devs)
        p90 = _percentile(abs_devs, 90)

        result["overall"] = {
            "count": len(devs),
            "MAD": round(mad, 4),
            "signed_mean": round(signed_mean, 4),
            "median_abs": round(p50, 4),
            "P90_abs": round(p90, 4),
        }

        # within-threshold rates
        thresholds = [0.1, 0.3, 0.5, 1.0, 2.0, 5.0]
        within = {}
        for th in thresholds:
            cnt = sum(1 for d in abs_devs if d <= th)
            within[f"within_{th}pp"] = round(cnt / len(abs_devs) * 100, 2)
        result["within_thresholds"] = within

        self.stdout.write(f"  전체 MAD: {mad:.4f}%p, signed mean: {signed_mean:+.4f}%p")
        self.stdout.write(f"  P50: {p50:.4f}%p, P90: {p90:.4f}%p")
        self.stdout.write(f"  0.5%p 이내: {within.get('within_0.5pp', 0):.1f}%, "
                          f"1.0%p 이내: {within.get('within_1.0pp', 0):.1f}%")

        # 연도별 트렌드
        by_year = defaultdict(list)
        for r in data:
            if r["rate_dev"] is not None and r["year"]:
                by_year[r["year"]].append(abs(r["rate_dev"]))
        year_trend = {}
        self.stdout.write("  연도별 MAD:")
        for y in sorted(by_year):
            m = _safe_mean(by_year[y])
            year_trend[y] = {
                "count": len(by_year[y]),
                "MAD": round(m, 4),
            }
            self.stdout.write(f"    {y}: MAD {m:.4f}%p ({len(by_year[y])}건)")
        result["by_year_trend"] = year_trend

        # MAD slope (simple linear regression)
        if len(year_trend) >= 2:
            years = sorted(year_trend.keys())
            mads = [year_trend[y]["MAD"] for y in years]
            n = len(years)
            x_mean = sum(years) / n
            y_mean = sum(mads) / n
            ss_xy = sum((years[i] - x_mean) * (mads[i] - y_mean) for i in range(n))
            ss_xx = sum((years[i] - x_mean) ** 2 for i in range(n))
            slope = ss_xy / ss_xx if ss_xx else 0
            result["mad_slope_per_year"] = round(slope, 4)
            improving = "나아지고 있음" if slope < 0 else "나빠지고 있음"
            self.stdout.write(f"  MAD 추세: {slope:+.4f}/년 ({improving})")

        # TABLE별 정확도
        by_table = defaultdict(list)
        for r in data:
            if r["rate_dev"] is not None and r["table_type"]:
                by_table[r["table_type"]].append(r["rate_dev"])
        table_accuracy = {}
        self.stdout.write("  TABLE별 정확도:")
        for t in sorted(by_table):
            ds = by_table[t]
            ads = [abs(d) for d in ds]
            table_accuracy[t] = {
                "count": len(ds),
                "MAD": round(_safe_mean(ads), 4),
                "signed_mean": round(_safe_mean(ds), 4),
                "stdev": round(_safe_stdev(ds), 4),
            }
            self.stdout.write(
                f"    {t}: MAD {_safe_mean(ads):.4f}, "
                f"signed {_safe_mean(ds):+.4f}, n={len(ds)}"
            )
        result["by_table"] = table_accuracy

        # 과투찰 vs 저투찰
        over = sum(1 for d in devs if d > 0)
        under = sum(1 for d in devs if d < 0)
        exact = sum(1 for d in devs if d == 0)
        result["over_under"] = {
            "over_bid": over,
            "under_bid": under,
            "exact": exact,
            "over_pct": round(over / len(devs) * 100, 2),
            "under_pct": round(under / len(devs) * 100, 2),
        }
        self.stdout.write(f"  과투찰: {over}건({over/len(devs)*100:.1f}%), "
                          f"저투찰: {under}건({under/len(devs)*100:.1f}%)")

        if not self.no_charts:
            self._chart_task1(result)

        return result

    # ──────────────────────────────────────────────
    # Task 2: TABLE별 심층 분석
    # ──────────────────────────────────────────────

    def _task2_table_deep(self) -> dict:
        data = self.data
        result = {}

        tables = sorted(set(r["table_type"] for r in data if r["table_type"]))

        # 통과율 + 연도별 추이
        pass_rates = {}
        for t in tables:
            t_rows = [r for r in self.floor_known if r["table_type"] == t]
            if not t_rows:
                continue
            passed = sum(1 for r in t_rows if r["passed_floor"])
            by_year = defaultdict(lambda: {"total": 0, "passed": 0})
            for r in t_rows:
                if r["year"]:
                    by_year[r["year"]]["total"] += 1
                    if r["passed_floor"]:
                        by_year[r["year"]]["passed"] += 1
            yearly = {}
            for y in sorted(by_year):
                info = by_year[y]
                yearly[y] = round(
                    info["passed"] / info["total"] * 100, 2
                ) if info["total"] else 0
            pass_rates[t] = {
                "total": len(t_rows),
                "passed": passed,
                "rate": round(passed / len(t_rows) * 100, 2),
                "by_year": yearly,
            }
        result["pass_rates"] = pass_rates

        self.stdout.write("  TABLE별 하한 통과율:")
        for t, info in sorted(pass_rates.items()):
            self.stdout.write(
                f"    {t}: {info['rate']:.1f}% "
                f"({info['passed']}/{info['total']})"
            )

        # 편차 분포 (0.1%p bin)
        deviation_dist = {}
        for t in tables:
            devs = [r["rate_dev"] for r in data
                    if r["table_type"] == t and r["rate_dev"] is not None]
            if not devs:
                continue
            bins = defaultdict(int)
            for d in devs:
                b = round(round(d * 10) / 10, 1)
                bins[b] += 1
            deviation_dist[t] = {
                "count": len(devs),
                "MAD": round(_safe_mean([abs(d) for d in devs]), 4),
                "bins": dict(sorted(bins.items())),
            }
        result["deviation_distribution"] = deviation_dist

        # 최적 조정 시뮬: delta -2~+2 스캔 (0.01%p 단위)
        optimal_shift = {}
        for t in tables:
            devs = [r["rate_dev"] for r in data
                    if r["table_type"] == t and r["rate_dev"] is not None]
            if not devs:
                continue
            best_delta = 0.0
            best_mad = _safe_mean([abs(d) for d in devs])
            for delta_100 in range(-200, 201):
                delta = delta_100 / 100.0
                shifted = [d + delta for d in devs]
                m = _safe_mean([abs(s) for s in shifted])
                if m < best_mad:
                    best_mad = m
                    best_delta = delta
            optimal_shift[t] = {
                "current_MAD": round(_safe_mean([abs(d) for d in devs]), 4),
                "optimal_delta": round(best_delta, 2),
                "optimal_MAD": round(best_mad, 4),
                "improvement": round(
                    _safe_mean([abs(d) for d in devs]) - best_mad, 4
                ),
            }
        result["optimal_shift"] = optimal_shift

        self.stdout.write("  최적 조정 시뮬:")
        for t, info in sorted(optimal_shift.items()):
            self.stdout.write(
                f"    {t}: delta={info['optimal_delta']:+.2f}%p, "
                f"MAD {info['current_MAD']:.4f} -> {info['optimal_MAD']:.4f} "
                f"(-{info['improvement']:.4f})"
            )

        # Near-miss 정량화
        near_miss = {}
        for t in tables:
            devs = [abs(r["rate_dev"]) for r in data
                    if r["table_type"] == t and r["rate_dev"] is not None]
            if not devs:
                continue
            thresholds = [0.1, 0.3, 0.5, 1.0]
            nm = {}
            for th in thresholds:
                cnt = sum(1 for d in devs if d < th)
                nm[f"within_{th}pp"] = {
                    "count": cnt,
                    "pct": round(cnt / len(devs) * 100, 2),
                }
            near_miss[t] = nm
        result["near_miss"] = near_miss

        if not self.no_charts:
            self._chart_task2(result)

        return result

    # ──────────────────────────────────────────────
    # Task 3: 시계열 + 제도 변경
    # ──────────────────────────────────────────────

    def _task3_timeseries(self) -> dict:
        data = self.data
        result = {}

        # 분기별 집계
        by_quarter = defaultdict(lambda: {
            "count": 0, "passed": 0, "devs": [], "rank1_rates": [],
        })
        for r in data:
            q = r["quarter"]
            if not q:
                continue
            by_quarter[q]["count"] += 1
            if r["floor_diff"] is not None and r["floor_diff"] >= 0:
                by_quarter[q]["passed"] += 1
            if r["rate_dev"] is not None:
                by_quarter[q]["devs"].append(abs(r["rate_dev"]))
            if r["rank1_rate"] is not None:
                by_quarter[q]["rank1_rates"].append(r["rank1_rate"])

        quarterly = {}
        for q in sorted(by_quarter):
            info = by_quarter[q]
            floor_total = sum(
                1 for r in self.floor_known if r["quarter"] == q
            )
            quarterly[q] = {
                "count": info["count"],
                "pass_rate": round(
                    info["passed"] / floor_total * 100, 2
                ) if floor_total else None,
                "MAD": round(_safe_mean(info["devs"]), 4) if info["devs"] else None,
                "rank1_rate_mean": round(
                    _safe_mean(info["rank1_rates"]), 4
                ) if info["rank1_rates"] else None,
            }
        result["quarterly"] = quarterly

        self.stdout.write("  분기별 요약:")
        for q, info in sorted(quarterly.items()):
            pr = f"{info['pass_rate']:.1f}%" if info['pass_rate'] is not None else "N/A"
            mad = f"{info['MAD']:.4f}" if info['MAD'] is not None else "N/A"
            self.stdout.write(
                f"    {q}: {info['count']}건, pass {pr}, MAD {mad}"
            )

        # 3개월 이동평균
        quarters = sorted(quarterly.keys())
        if len(quarters) >= 3:
            moving_avg = {}
            mad_values = [quarterly[q]["MAD"] for q in quarters]
            for i in range(2, len(quarters)):
                window = [v for v in mad_values[i-2:i+1] if v is not None]
                if window:
                    moving_avg[quarters[i]] = round(_safe_mean(window), 4)
            result["mad_moving_avg_3q"] = moving_avg

        # 2026.1.30 전후 비교
        pre = [r for r in data if r["regime"] == "pre" and r["rate_dev"] is not None]
        post = [r for r in data if r["regime"] == "post" and r["rate_dev"] is not None]
        regime_compare = {
            "pre": {
                "count": len(pre),
                "MAD": round(_safe_mean([abs(r["rate_dev"]) for r in pre]), 4) if pre else None,
            },
            "post": {
                "count": len(post),
                "MAD": round(_safe_mean([abs(r["rate_dev"]) for r in post]), 4) if post else None,
            },
        }
        if len(post) < 30:
            regime_compare["warning"] = f"post 표본 {len(post)}건 — 통계적 유의성 낮음"
            self.stdout.write(
                f"  ⚠️ 제도 변경 후 표본: {len(post)}건 (유의성 낮음)"
            )
        result["regime_comparison"] = regime_compare

        self.stdout.write(f"  제도 변경 전: {len(pre)}건, 후: {len(post)}건")
        if pre:
            self.stdout.write(
                f"    pre MAD: {regime_compare['pre']['MAD']:.4f}%p"
            )
        if post and regime_compare["post"]["MAD"] is not None:
            self.stdout.write(
                f"    post MAD: {regime_compare['post']['MAD']:.4f}%p"
            )

        # 낙찰자 사정율 시계열
        rank1_ts = {}
        for q in quarters:
            rates = [
                r["rank1_rate"] for r in data
                if r["quarter"] == q and r["rank1_rate"] is not None
            ]
            if rates:
                rank1_ts[q] = {
                    "mean": round(_safe_mean(rates), 4),
                    "stdev": round(_safe_stdev(rates), 4),
                    "count": len(rates),
                }
        result["rank1_rate_timeseries"] = rank1_ts

        if not self.no_charts:
            self._chart_task3(result)

        return result

    # ──────────────────────────────────────────────
    # Task 4: 경쟁업체 프로파일링
    # ──────────────────────────────────────────────

    def _task4_competitors(self) -> dict:
        data = self.data
        result = {}

        # Top 30 빈도
        rank1_counter = Counter(
            r["rank1_company"] for r in data
            if r["rank1_company"]
        )
        top30 = rank1_counter.most_common(30)
        result["top30_frequency"] = [
            {"company": c, "wins": w} for c, w in top30
        ]
        total_with_rank1 = sum(rank1_counter.values())

        self.stdout.write("  Top 10 낙찰업체:")
        for c, w in top30[:10]:
            self.stdout.write(
                f"    {c}: {w}건 ({w/total_with_rank1*100:.1f}%)"
            )

        # 상위 10개 점유율
        top10_wins = sum(w for _, w in top30[:10])
        result["top10_share"] = round(
            top10_wins / total_with_rank1 * 100, 2
        ) if total_with_rank1 else 0
        self.stdout.write(
            f"  상위 10개 점유율: {result['top10_share']:.1f}%"
        )

        # TABLE별 지배업체
        table_dominance = {}
        for t in sorted(set(r["table_type"] for r in data if r["table_type"])):
            t_rows = [r for r in data
                      if r["table_type"] == t and r["rank1_company"]]
            if not t_rows:
                continue
            cnt = Counter(r["rank1_company"] for r in t_rows)
            top3 = cnt.most_common(3)
            table_dominance[t] = [
                {"company": c, "wins": w, "pct": round(w / len(t_rows) * 100, 2)}
                for c, w in top3
            ]
        result["table_dominance"] = table_dominance

        # 반복 낙찰자 사정율 일관성
        company_rates = defaultdict(list)
        for r in data:
            if r["rank1_company"] and r["rank1_rate"] is not None:
                company_rates[r["rank1_company"]].append(r["rank1_rate"])

        consistency = []
        for c, rates in company_rates.items():
            if len(rates) >= 3:
                consistency.append({
                    "company": c,
                    "count": len(rates),
                    "mean": round(_safe_mean(rates), 4),
                    "stdev": round(_safe_stdev(rates), 4),
                })
        consistency.sort(key=lambda x: x["count"], reverse=True)
        result["winner_consistency"] = consistency[:20]

        self.stdout.write("  반복 낙찰자 사정율 일관성 (Top 5):")
        for info in consistency[:5]:
            self.stdout.write(
                f"    {info['company']}: "
                f"mean={info['mean']:.4f}, std={info['stdev']:.4f} "
                f"(n={info['count']})"
            )

        # 발주처 x 업체 교차
        org_company = defaultdict(lambda: Counter())
        for r in data:
            if r["org"] and r["rank1_company"]:
                org_company[r["org"]][r["rank1_company"]] += 1

        # Top 10 발주처의 top 업체
        org_counts = Counter(r["org"] for r in data if r["org"])
        cross = {}
        for org, _ in org_counts.most_common(10):
            top = org_company[org].most_common(3)
            cross[org] = [{"company": c, "wins": w} for c, w in top]
        result["org_company_cross"] = cross

        if not self.no_charts:
            self._chart_task4(result)

        return result

    # ──────────────────────────────────────────────
    # Task 5: 금액대 + 발주처 세분화
    # ──────────────────────────────────────────────

    def _task5_segmentation(self) -> dict:
        data = self.data
        result = {}

        # 금액대별
        amt_stats = {}
        for seg_name, lo, hi in AMT_SEGMENTS:
            seg_rows = [r for r in data if r["base_amt"] and lo <= r["base_amt"] < hi]
            if not seg_rows:
                continue
            floor_rows = [r for r in seg_rows if r["floor_diff"] is not None]
            passed = sum(1 for r in floor_rows if r["floor_diff"] >= 0)
            devs = [abs(r["rate_dev"]) for r in seg_rows if r["rate_dev"] is not None]
            rank1_rates = [r["rank1_rate"] for r in seg_rows if r["rank1_rate"] is not None]
            amt_stats[seg_name] = {
                "count": len(seg_rows),
                "pass_rate": round(passed / len(floor_rows) * 100, 2) if floor_rows else None,
                "MAD": round(_safe_mean(devs), 4) if devs else None,
                "rank1_rate_mean": round(_safe_mean(rank1_rates), 4) if rank1_rates else None,
            }
        result["by_amount"] = amt_stats

        self.stdout.write("  금액대별:")
        for seg, info in amt_stats.items():
            pr = f"{info['pass_rate']:.1f}%" if info['pass_rate'] is not None else "N/A"
            mad = f"{info['MAD']:.4f}" if info['MAD'] is not None else "N/A"
            self.stdout.write(
                f"    {seg}: {info['count']}건, pass {pr}, MAD {mad}"
            )

        # 발주처 Top 20
        org_counter = Counter(r["org"] for r in data if r["org"])
        top20_orgs = org_counter.most_common(20)
        org_stats = []
        for org, cnt in top20_orgs:
            org_rows = [r for r in data if r["org"] == org]
            devs = [abs(r["rate_dev"]) for r in org_rows if r["rate_dev"] is not None]
            floor_rows = [r for r in org_rows if r["floor_diff"] is not None]
            passed = sum(1 for r in floor_rows if r["floor_diff"] >= 0)
            org_stats.append({
                "org": org,
                "count": cnt,
                "MAD": round(_safe_mean(devs), 4) if devs else None,
                "pass_rate": round(passed / len(floor_rows) * 100, 2) if floor_rows else None,
            })
        result["top20_orgs"] = org_stats

        self.stdout.write("  발주처 Top 10:")
        for info in org_stats[:10]:
            pr = f"{info['pass_rate']:.1f}%" if info['pass_rate'] is not None else "N/A"
            self.stdout.write(f"    {info['org'][:30]}: {info['count']}건, pass {pr}")

        # 업종별
        sector_counter = Counter(r["sector"] for r in data if r["sector"])
        sector_stats = []
        for sec, cnt in sector_counter.most_common(15):
            sec_rows = [r for r in data if r["sector"] == sec]
            floor_rows = [r for r in sec_rows if r["floor_diff"] is not None]
            passed = sum(1 for r in floor_rows if r["floor_diff"] >= 0)
            sector_stats.append({
                "sector": sec,
                "count": cnt,
                "pass_rate": round(passed / len(floor_rows) * 100, 2) if floor_rows else None,
            })
        result["by_sector"] = sector_stats

        if not self.no_charts:
            self._chart_task5(result)

        return result

    # ──────────────────────────────────────────────
    # Task 6: 개선 포텐셜 정량화
    # ──────────────────────────────────────────────

    def _task6_potential(self) -> dict:
        data = self.data
        result = {}

        # Near-miss 워터폴: 하한 통과했지만 1순위 못 한 건
        # 임계값별 "통과했는데 |dev| < threshold" 건수
        thresholds = [0.1, 0.3, 0.5, 1.0, 2.0]
        waterfall = {}
        for th in thresholds:
            # 하한 통과 + 편차 th 이내 but rank != 1
            near = [
                r for r in self.passed
                if r["rate_dev"] is not None
                and abs(r["rate_dev"]) <= th
                and r["our_rank"] is not None
                and r["our_rank"] != 1
            ]
            est_sum = sum(
                r["est_price"] for r in near
                if r["est_price"] is not None
            )
            waterfall[f"within_{th}pp"] = {
                "count": len(near),
                "est_price_sum_eouk": round(est_sum / UNIT_EOUK, 1),
            }
        result["near_miss_waterfall"] = waterfall

        self.stdout.write("  Near-miss 워터폴 (하한통과 + |dev|<th + rank!=1):")
        for th_key, info in waterfall.items():
            self.stdout.write(
                f"    {th_key}: {info['count']}건, "
                f"예정가격합 {info['est_price_sum_eouk']:.1f}억"
            )

        # 하한미달 회피 가능 건수
        floor_failed = self.failed
        avoidable = {}
        for th in [0.5, 1.0, 2.0, 5.0]:
            # 하한미달 중 편차(= 부족분) < threshold
            close = [
                r for r in floor_failed
                if r["rate_dev"] is not None
                and r["floor_diff"] is not None
                and abs(r["floor_diff"]) <= r["est_price"] * th / 100
                if r["est_price"]
            ]
            avoidable[f"gap_within_{th}pp"] = len(close)
        result["floor_fail_avoidable"] = avoidable

        self.stdout.write(f"  하한미달 전체: {len(floor_failed)}건")
        for k, v in avoidable.items():
            self.stdout.write(f"    {k}: {v}건 회피 가능")

        # 잠재 매출: 하한미달 건의 예정가격 합산
        fail_est_sum = sum(
            r["est_price"] for r in floor_failed
            if r["est_price"] is not None
        )
        result["lost_revenue_eouk"] = round(fail_est_sum / UNIT_EOUK, 1)
        self.stdout.write(
            f"  하한미달 잠재 매출: {result['lost_revenue_eouk']:.1f}억"
        )

        # 정확도 개선 누적 곡선
        all_devs = sorted(
            abs(r["rate_dev"]) for r in data if r["rate_dev"] is not None
        )
        if all_devs:
            cumulative = []
            steps = [i * 0.1 for i in range(51)]  # 0~5%p
            for step in steps:
                cnt = sum(1 for d in all_devs if d <= step)
                cumulative.append({
                    "threshold": round(step, 1),
                    "cumulative_pct": round(cnt / len(all_devs) * 100, 2),
                })
            result["accuracy_cumulative"] = cumulative

        if not self.no_charts:
            self._chart_task6(result)

        return result

    # ──────────────────────────────────────────────
    # Task 7: 종합 요약
    # ──────────────────────────────────────────────

    def _task7_summary(self) -> dict:
        data = self.data
        result = {}

        devs = [r["rate_dev"] for r in data if r["rate_dev"] is not None]
        abs_devs = [abs(d) for d in devs]
        floor_total = len(self.floor_known)
        passed_cnt = len(self.passed)

        result["headline"] = {
            "total_bids": len(data),
            "period": "2021.1 ~ 2026.3",
            "MAD": round(_safe_mean(abs_devs), 4) if abs_devs else None,
            "pass_rate": round(
                passed_cnt / floor_total * 100, 2
            ) if floor_total else None,
            "signed_mean": round(_safe_mean(devs), 4) if devs else None,
        }

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("  종합 요약: 인포21C 5년 성적표")
        self.stdout.write("=" * 60)
        self.stdout.write(f"  분석 대상: {len(data):,}건 ({result['headline']['period']})")
        self.stdout.write(
            f"  전체 MAD: {result['headline']['MAD']:.4f}%p"
        ) if result["headline"]["MAD"] else None
        self.stdout.write(
            f"  하한 통과율: {result['headline']['pass_rate']:.1f}% "
            f"({passed_cnt}/{floor_total})"
        ) if result["headline"]["pass_rate"] is not None else None

        # TABLE별 권장 delta
        tables = sorted(set(r["table_type"] for r in data if r["table_type"]))
        table_recommendations = {}
        for t in tables:
            t_devs = [r["rate_dev"] for r in data
                      if r["table_type"] == t and r["rate_dev"] is not None]
            if not t_devs:
                continue
            bias = _safe_mean(t_devs)
            current_mad = _safe_mean([abs(d) for d in t_devs])
            # MAD-optimal delta scan (0.01%p)
            best_delta = 0.0
            best_mad = current_mad
            for d100 in range(-200, 201):
                delta = d100 / 100.0
                m = _safe_mean([abs(v + delta) for v in t_devs])
                if m < best_mad:
                    best_mad = m
                    best_delta = delta
            table_recommendations[t] = {
                "count": len(t_devs),
                "bias": round(bias, 4),
                "recommended_delta": round(best_delta, 2),
                "current_MAD": round(current_mad, 4),
                "expected_MAD": round(best_mad, 4),
                "improvement": round(current_mad - best_mad, 4),
            }
        result["table_recommendations"] = table_recommendations

        self.stdout.write("\n  TABLE별 권장 조정:")
        for t, info in sorted(table_recommendations.items()):
            self.stdout.write(
                f"    {t}: delta={info['recommended_delta']:+.2f}%p, "
                f"MAD {info['current_MAD']:.4f} -> {info['expected_MAD']:.4f} "
                f"(-{info['improvement']:.4f})"
            )

        # BidCompass 킬러 피처 근거
        self.stdout.write("\n  BidCompass 킬러 피처 근거:")
        if abs_devs:
            within_1 = sum(1 for d in abs_devs if d <= 1.0)
            self.stdout.write(
                f"    인포21C 1%p 이내 적중: "
                f"{within_1/len(abs_devs)*100:.1f}% ({within_1}/{len(abs_devs)})"
            )
        if result["headline"]["pass_rate"] is not None:
            self.stdout.write(
                f"    하한 통과율: {result['headline']['pass_rate']:.1f}% "
                f"(미달 {floor_total - passed_cnt}건 = 잠재 매출 손실)"
            )
        total_bias = _safe_mean(devs) if devs else 0
        direction = "과투찰 경향" if total_bias > 0 else "저투찰 경향"
        self.stdout.write(f"    전체 편향: {total_bias:+.4f}%p ({direction})")
        self.stdout.write(
            "    -> 편향 보정만으로 MAD 개선 가능, TABLE별 미세조정 추가 여지"
        )

        result["killer_features"] = {
            "info21c_within_1pp": round(
                sum(1 for d in abs_devs if d <= 1.0) / len(abs_devs) * 100, 2
            ) if abs_devs else None,
            "pass_rate": result["headline"]["pass_rate"],
            "overall_bias": round(total_bias, 4),
            "bias_direction": direction,
        }

        return result

    # ──────────────────────────────────────────────
    # Charts
    # ──────────────────────────────────────────────

    def _init_matplotlib(self):
        """matplotlib lazy import + 한글폰트 설정. 실패 시 None 반환."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
        except ImportError:
            self.stderr.write("  matplotlib 미설치 — 차트 생략")
            return None

        plt.rcParams["axes.unicode_minus"] = False
        for font_name in ["AppleGothic", "Malgun Gothic", "NanumGothic"]:
            if any(font_name in f.name for f in fm.fontManager.ttflist):
                plt.rcParams["font.family"] = font_name
                break

        return plt

    def _chart_dir(self) -> Path:
        d = BASE_DIR / "data" / "collected" / "charts"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _save_chart(self, fig, filename: str):
        fig.savefig(self._chart_dir() / filename, dpi=150, bbox_inches="tight")
        import matplotlib.pyplot as plt
        plt.close(fig)
        self.stdout.write(f"  차트: {filename}")

    def _chart_task1(self, result: dict):
        """Task 1 차트: 연도별 정확도 트렌드 + TABLE별 정확도."""
        plt = self._init_matplotlib()
        if not plt:
            return

        try:
            # Chart 1: 연도별 MAD 트렌드
            year_data = result.get("by_year_trend", {})
            if year_data:
                fig, ax = plt.subplots(figsize=(10, 5))
                years = sorted(year_data.keys())
                mads = [year_data[y]["MAD"] for y in years]
                counts = [year_data[y]["count"] for y in years]

                ax.bar(
                    [str(y) for y in years], counts,
                    alpha=0.3, color="steelblue", label="건수",
                )
                ax2 = ax.twinx()
                ax2.plot(
                    [str(y) for y in years], mads,
                    "ro-", linewidth=2, markersize=8, label="MAD",
                )
                ax.set_xlabel("연도")
                ax.set_ylabel("건수")
                ax2.set_ylabel("MAD (%p)")
                ax.set_title("인포21C 연도별 정확도 트렌드")
                ax.legend(loc="upper left")
                ax2.legend(loc="upper right")
                fig.tight_layout()
                self._save_chart(fig, "info21c_accuracy_trend.png")

            # Chart 2: TABLE별 정확도
            table_data = result.get("by_table", {})
            if table_data:
                fig, ax = plt.subplots(figsize=(10, 5))
                tables = sorted(table_data.keys())
                mads = [table_data[t]["MAD"] for t in tables]
                signed = [table_data[t]["signed_mean"] for t in tables]

                x = range(len(tables))
                width = 0.35
                ax.bar(
                    [i - width / 2 for i in x], mads, width,
                    label="MAD", color="coral",
                )
                ax.bar(
                    [i + width / 2 for i in x], signed, width,
                    label="Signed Mean", color="steelblue",
                )
                ax.set_xticks(list(x))
                ax.set_xticklabels(tables)
                ax.set_ylabel("%p")
                ax.set_title("인포21C TABLE별 정확도")
                ax.legend()
                ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
                fig.tight_layout()
                self._save_chart(fig, "info21c_accuracy_by_table.png")

        except Exception as e:
            self.stderr.write(f"  차트 실패 (task1): {e}")

    def _chart_task2(self, result: dict):
        """Task 2 차트: TABLE별 편차 분포 히스토그램 (5-panel)."""
        plt = self._init_matplotlib()
        if not plt:
            return

        try:
            dev_dist = result.get("deviation_distribution", {})
            tables = sorted(dev_dist.keys())
            if not tables:
                return

            n = len(tables)
            fig, axes = plt.subplots(1, n, figsize=(4 * n, 4), sharey=True)
            if n == 1:
                axes = [axes]

            for ax, t in zip(axes, tables):
                bins = dev_dist[t]["bins"]
                xs = sorted(bins.keys())
                ys = [bins[x] for x in xs]
                ax.bar(xs, ys, width=0.09, color="steelblue", alpha=0.7)
                ax.set_title(f"{t} (MAD={dev_dist[t]['MAD']:.3f})")
                ax.set_xlabel("편차 (%p)")
                ax.axvline(x=0, color="red", linestyle="--", linewidth=0.8)

            axes[0].set_ylabel("건수")
            fig.suptitle("인포21C TABLE별 사정율 편차 분포 (0.1%p bin)", y=1.02)
            fig.tight_layout()
            self._save_chart(fig, "table_deviation_distribution.png")

        except Exception as e:
            self.stderr.write(f"  차트 실패 (task2): {e}")

    def _chart_task3(self, result: dict):
        """Task 3 차트: 분기별 시계열."""
        plt = self._init_matplotlib()
        if not plt:
            return

        try:
            quarterly = result.get("quarterly", {})
            if not quarterly:
                return

            quarters = sorted(quarterly.keys())
            counts = [quarterly[q]["count"] for q in quarters]
            pass_rates = [quarterly[q]["pass_rate"] for q in quarters]
            mads = [quarterly[q]["MAD"] for q in quarters]

            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

            ax1.bar(quarters, counts, color="steelblue", alpha=0.7)
            ax1.set_ylabel("건수")
            ax1.set_title("분기별 건수")

            valid_pr = [(q, v) for q, v in zip(quarters, pass_rates) if v is not None]
            if valid_pr:
                ax2.plot(
                    [q for q, _ in valid_pr],
                    [v for _, v in valid_pr],
                    "go-", linewidth=1.5, markersize=5,
                )
            ax2.set_ylabel("통과율 (%)")
            ax2.set_title("분기별 하한 통과율")

            valid_mad = [(q, v) for q, v in zip(quarters, mads) if v is not None]
            if valid_mad:
                ax3.plot(
                    [q for q, _ in valid_mad],
                    [v for _, v in valid_mad],
                    "ro-", linewidth=1.5, markersize=5,
                )
            ax3.set_ylabel("MAD (%p)")
            ax3.set_title("분기별 MAD")

            # regime line
            for ax in [ax1, ax2, ax3]:
                # Find quarter closest to 2026Q1
                if "2026Q1" in quarters:
                    ax.axvline(
                        x="2026Q1", color="purple", linestyle="--",
                        linewidth=1, alpha=0.7,
                    )

            plt.xticks(rotation=45, ha="right")
            fig.tight_layout()
            self._save_chart(fig, "time_series_quarterly.png")

        except Exception as e:
            self.stderr.write(f"  차트 실패 (task3): {e}")

    def _chart_task4(self, result: dict):
        """Task 4 차트: 경쟁업체 Top 15 + 사정율 산점도."""
        plt = self._init_matplotlib()
        if not plt:
            return

        try:
            top30 = result.get("top30_frequency", [])
            if not top30:
                return

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

            # 막대: Top 15
            display = top30[:15]
            names = [d["company"][:8] for d in display]
            wins = [d["wins"] for d in display]
            ax1.barh(list(range(len(names))), wins, color="steelblue", alpha=0.7)
            ax1.set_yticks(list(range(len(names))))
            ax1.set_yticklabels(names)
            ax1.invert_yaxis()
            ax1.set_xlabel("낙찰 횟수")
            ax1.set_title("Top 15 낙찰업체")

            # 산점도: 반복 낙찰자 사정율 일관성
            consistency = result.get("winner_consistency", [])
            if consistency:
                cs = [c["count"] for c in consistency[:20]]
                means = [c["mean"] for c in consistency[:20]]
                stds = [c["stdev"] for c in consistency[:20]]
                ax2.scatter(means, stds, s=[c * 20 for c in cs], alpha=0.6, c="coral")
                ax2.set_xlabel("평균 사정율")
                ax2.set_ylabel("사정율 표준편차")
                ax2.set_title("반복 낙찰자 사정율 일관성")
                for i, c in enumerate(consistency[:5]):
                    ax2.annotate(
                        c["company"][:6],
                        (means[i], stds[i]),
                        fontsize=8,
                    )

            fig.tight_layout()
            self._save_chart(fig, "competitor_landscape.png")

        except Exception as e:
            self.stderr.write(f"  차트 실패 (task4): {e}")

    def _chart_task5(self, result: dict):
        """Task 5 차트: 금액대별 세분화."""
        plt = self._init_matplotlib()
        if not plt:
            return

        try:
            amt_data = result.get("by_amount", {})
            if not amt_data:
                return

            segs = list(amt_data.keys())
            counts = [amt_data[s]["count"] for s in segs]
            pass_rates = [amt_data[s]["pass_rate"] for s in segs]
            mads = [amt_data[s]["MAD"] for s in segs]

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

            x = range(len(segs))
            ax1.bar(x, counts, color="steelblue", alpha=0.7)
            ax1_twin = ax1.twinx()
            valid_pr = [(i, v) for i, v in enumerate(pass_rates) if v is not None]
            if valid_pr:
                ax1_twin.plot(
                    [i for i, _ in valid_pr],
                    [v for _, v in valid_pr],
                    "go-", linewidth=2, markersize=8,
                )
            ax1.set_xticks(list(x))
            ax1.set_xticklabels(segs)
            ax1.set_ylabel("건수")
            ax1_twin.set_ylabel("통과율 (%)")
            ax1.set_title("금액대별 건수 + 하한 통과율")

            valid_mad = [(i, v) for i, v in enumerate(mads) if v is not None]
            if valid_mad:
                ax2.bar(
                    [i for i, _ in valid_mad],
                    [v for _, v in valid_mad],
                    color="coral", alpha=0.7,
                )
            ax2.set_xticks(list(x))
            ax2.set_xticklabels(segs)
            ax2.set_ylabel("MAD (%p)")
            ax2.set_title("금액대별 MAD")

            fig.tight_layout()
            self._save_chart(fig, "amount_segmentation.png")

        except Exception as e:
            self.stderr.write(f"  차트 실패 (task5): {e}")

    def _chart_task6(self, result: dict):
        """Task 6 차트: 워터폴 + 누적 곡선."""
        plt = self._init_matplotlib()
        if not plt:
            return

        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # 워터폴
            wf = result.get("near_miss_waterfall", {})
            if wf:
                labels = list(wf.keys())
                counts = [wf[k]["count"] for k in labels]
                ax1.bar(labels, counts, color="coral", alpha=0.7)
                ax1.set_ylabel("건수")
                ax1.set_title("Near-miss 워터폴\n(하한통과 + |dev|<th + rank!=1)")
                ax1.tick_params(axis="x", rotation=30)

            # 누적 곡선
            cum = result.get("accuracy_cumulative", [])
            if cum:
                thresholds = [c["threshold"] for c in cum]
                pcts = [c["cumulative_pct"] for c in cum]
                ax2.plot(thresholds, pcts, "b-", linewidth=2)
                ax2.fill_between(thresholds, pcts, alpha=0.1, color="blue")
                ax2.set_xlabel("편차 임계값 (%p)")
                ax2.set_ylabel("누적 비율 (%)")
                ax2.set_title("정확도 개선 누적 곡선")
                ax2.axhline(y=80, color="gray", linestyle="--", linewidth=0.5)
                ax2.axhline(y=90, color="gray", linestyle="--", linewidth=0.5)
                ax2.set_xlim(0, 5)
                ax2.set_ylim(0, 105)

            fig.tight_layout()
            self._save_chart(fig, "improvement_potential.png")

        except Exception as e:
            self.stderr.write(f"  차트 실패 (task6): {e}")

    # ──────────────────────────────────────────────
    # JSON 저장
    # ──────────────────────────────────────────────

    def _save_json(self, results: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "meta": {
                "command": "analyze_info21c_history",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "description": "인포21C 투찰성향 5년 EDA (2021~2026)",
            },
            **_clean(results),
        }

        path.write_text(
            json.dumps(
                report, ensure_ascii=False, indent=2, default=str,
            ),
            encoding="utf-8",
        )
        self.stdout.write(self.style.SUCCESS(f"\n  JSON 저장: {path}"))
