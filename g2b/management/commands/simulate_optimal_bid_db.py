"""BC-35: DB 기반 대규모 최적투찰 백테스트.

수집된 A값/복수예비가격(DB)로 최적투찰 엔진을 실행하여:
  - 최적 bid vs 1순위 bid 가격점수 비교
  - 기대점수 vs 실제점수 예측력 검증
  - 별표별 분석

⚠️ WorkType=CONSTRUCTION 가정 (DB에 work_type 필드 없음).
   전문공사(전기/정보통신/소방) 섞여 있으면 별표 라우팅 오류 가능.

사용:
    python manage.py simulate_optimal_bid_db --limit 5 --verbosity 2
    python manage.py simulate_optimal_bid_db
    python manage.py simulate_optimal_bid_db --output data/collected/optimal_bid_db_result.json
"""

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Q

from g2b.models import (
    BidApiAValue,
    BidApiCollectionLog,
    BidApiPrelimPrice,
    BidResult,
)
from g2b.services.bid_engine import (
    AValueItems,
    TableType,
    UNIT_EOUK,
    WorkType,
    calculate_a_value,
    get_floor_rate,
    select_table,
)
from g2b.services.optimal_bid import (
    OptimalBidInput,
    evaluate_bid,
    find_optimal_bid,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 5,030건 재현용 strict-sample 파라미터
STRICT_PRELIM_COUNT = 15
STRICT_BID_RATE_MIN = 0.80
STRICT_BID_RATE_MAX = 1.00

# 금액대 버킷 (별표 경계와 동일, 원 단위)
AMOUNT_BUCKETS: list[tuple[int, int, str]] = [
    (0,                 2 * UNIT_EOUK,    "<2억"),
    (2 * UNIT_EOUK,     3 * UNIT_EOUK,    "2~3억"),
    (3 * UNIT_EOUK,     10 * UNIT_EOUK,   "3~10억"),
    (10 * UNIT_EOUK,    50 * UNIT_EOUK,   "10~50억"),
    (50 * UNIT_EOUK,    100 * UNIT_EOUK,  "50~100억"),
    (100 * UNIT_EOUK,   10**18,           ">=100억"),
]

# 투찰자수 버킷
BIDDER_BUCKETS: list[tuple[int, int, str]] = [
    (1, 2,    "1-2명"),
    (3, 5,    "3-5명"),
    (6, 10,   "6-10명"),
    (11, 20,  "11-20명"),
    (21, 50,  "21-50명"),
    (51, 10**9, "51명+"),
]

RANK1_QUERY_BATCH_SIZE = 1000


def _bucket_label(value: int, buckets: list[tuple[int, int, str]]) -> str:
    """value를 [lo, hi] (양 끝 포함) 라벨에 매칭. 미매칭은 'unknown'."""
    if value is None:
        return "unknown"
    for lo, hi, label in buckets:
        if lo <= value <= hi:
            return label
    return "unknown"


def _amount_bucket(price: int) -> str:
    """[lo, hi) 경계로 금액대 라벨 반환."""
    if price is None or price <= 0:
        return "unknown"
    for lo, hi, label in AMOUNT_BUCKETS:
        if lo <= price < hi:
            return label
    return "unknown"


class Command(BaseCommand):
    help = "BC-35: DB 기반 대규모 최적투찰 백테스트"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=0,
            help="실행 건수 제한 (디버깅용, 0=전체)",
        )
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로",
        )
        parser.add_argument(
            "--strict-sample", action="store_true", default=False,
            help=(
                "5,030건 재현 표본 조건 적용: "
                "복수예비가격 정확히 15개 + 1순위 bid_rate 80~100%% + A값 보유"
            ),
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        output_path = options["output"]
        verbosity = options["verbosity"]
        strict_sample = options["strict_sample"]
        self._strict_sample = strict_sample

        if strict_sample:
            self.stdout.write(self.style.NOTICE(
                f"[strict-sample] 복수예비가격={STRICT_PRELIM_COUNT}개, "
                f"bid_rate∈[{STRICT_BID_RATE_MIN}, {STRICT_BID_RATE_MAX}]"
            ))

        # 1. 대상 공고 추출
        self.stdout.write("수집 완료 공고 목록 조회 중...")
        # strict-sample에서는 필터를 먼저 적용한 뒤 limit을 걸어야 표본이 흔들리지 않는다.
        target_limit = 0 if strict_sample and limit > 0 else limit
        targets = self._get_targets(target_limit)
        self.stdout.write(f"  백테스트 후보: {len(targets)}건")
        if strict_sample and limit > 0:
            self.stdout.write(f"  strict 처리 제한: {limit}건")

        if not targets:
            self.stdout.write(self.style.WARNING("대상 없음"))
            return

        # 2. 데이터 로드
        self.stdout.write("A값/복수예비가격/1순위 데이터 로드 중...")
        a_values_map = self._load_a_values(targets)
        prelim_map = self._load_prelim_prices(targets, strict_sample=strict_sample)
        rank1_map = self._load_rank1_data(targets)
        self.stdout.write(
            f"  A값: {len(a_values_map)}건, "
            f"복수예비가격: {len(prelim_map)}건, "
            f"1순위: {len(rank1_map)}건"
        )

        # 3. 백테스트 실행
        results = self._run_backtest(
            targets, a_values_map, prelim_map, rank1_map, verbosity,
            strict_sample=strict_sample,
            processed_limit=limit if strict_sample and limit > 0 else 0,
        )

        # 4. 리포트 출력
        self._print_summary(results)
        self._print_vs_rank1(results)
        self._print_prediction_accuracy(results)
        self._print_bid_rate_comparison(results)
        self._print_band_hit(results)
        self._print_floor_pass(results)
        self._print_by_table(results)
        self._print_by_amount_bucket(results)
        self._print_by_bidder_bucket(results)

        # 5. JSON 저장
        if output_path:
            self._save_json(results, output_path)

    # ──────────────────────────────────────────
    # 데이터 로드
    # ──────────────────────────────────────────

    def _get_targets(self, limit: int) -> list[tuple[str, str]]:
        """A값 + 복수예비가격 둘 다 수집 완료된 공고 목록."""
        qs = (
            BidApiCollectionLog.objects
            .filter(a_value_status="ok", prelim_status="ok")
            .values_list("bid_ntce_no", "bid_ntce_ord")
            .order_by("-bid_ntce_no")
        )
        if limit > 0:
            return list(qs[:limit])
        return list(qs)

    def _load_a_values(
        self, targets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], int]:
        """A값 DB → {(ntce_no, ntce_ord): a_value_int}. 불완전 건도 포함."""
        result = {}
        a_incomplete_count = 0
        for ntce_no, ntce_ord in targets:
            try:
                row = BidApiAValue.objects.get(
                    bid_ntce_no=ntce_no, bid_ntce_ord=ntce_ord,
                )
                items = AValueItems(
                    national_pension=row.national_pension,
                    health_insurance=row.health_insurance,
                    retirement_mutual_aid=row.retirement_mutual_aid,
                    long_term_care=row.long_term_care,
                    occupational_safety=row.occupational_safety,
                    safety_management=row.safety_management,
                    quality_management=row.quality_management,
                )
                a_value = calculate_a_value(items)

                # 불완전 건 카운트 (7개 중 0이 아닌 항목 < 3개)
                nonzero = sum(1 for f in [
                    row.national_pension, row.health_insurance,
                    row.retirement_mutual_aid, row.long_term_care,
                    row.occupational_safety, row.safety_management,
                    row.quality_management,
                ] if f > 0)
                if nonzero < 3:
                    a_incomplete_count += 1

                result[(ntce_no, ntce_ord)] = a_value
            except BidApiAValue.DoesNotExist:
                pass

        self._a_incomplete_count = a_incomplete_count
        return result

    def _load_prelim_prices(
        self,
        targets: list[tuple[str, str]],
        strict_sample: bool = False,
    ) -> dict[tuple[str, str], list[int]]:
        """복수예비가격 DB → {(ntce_no, ntce_ord): [basis_planned_price, ...]}.

        strict_sample=True 일 때만 정확히 15개 보유 건만 통과 (5,030건 재현).
        """
        min_required = STRICT_PRELIM_COUNT if strict_sample else 4
        result = {}
        for ntce_no, ntce_ord in targets:
            rows = list(
                BidApiPrelimPrice.objects
                .filter(
                    bid_ntce_no=ntce_no,
                    bid_ntce_ord=ntce_ord,
                    basis_planned_price__gt=0,
                )
                .order_by("sequence_no")
                .values_list("basis_planned_price", flat=True)
            )
            if strict_sample:
                if len(rows) != STRICT_PRELIM_COUNT:
                    continue
            elif len(rows) < min_required:
                continue
            result[(ntce_no, ntce_ord)] = rows
        return result

    def _load_rank1_data(
        self, targets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], dict]:
        """1순위(낙찰자) 데이터 로드. openg_rank='1' 필터."""
        from django.db import connection

        if not targets:
            return {}

        result = {}
        with connection.cursor() as cursor:
            for start in range(0, len(targets), RANK1_QUERY_BATCH_SIZE):
                batch = targets[start:start + RANK1_QUERY_BATCH_SIZE]
                placeholders = ", ".join(["(%s, %s)"] * len(batch))
                flat_params = []
                for ntce_no, ntce_ord in batch:
                    flat_params.extend([ntce_no, ntce_ord])

                sql = f"""
                    SELECT DISTINCT ON (bid_ntce_no, bid_ntce_ord)
                        bid_ntce_no, bid_ntce_ord,
                        presume_price, estimated_price, bid_amt, bidder_cnt
                    FROM g2b_bidresult
                    WHERE (bid_ntce_no, bid_ntce_ord) IN ({placeholders})
                      AND presume_price > 0
                      AND estimated_price > 0
                      AND success_lowest_rate > 0
                      AND bid_amt > 0
                      AND openg_rank = '1'
                    ORDER BY bid_ntce_no, bid_ntce_ord, bid_amt ASC
                """

                cursor.execute(sql, flat_params)
                for row in cursor.fetchall():
                    key = (row[0], row[1])
                    result[key] = {
                        "presume_price": row[2],
                        "estimated_price": row[3],
                        "rank1_bid_amt": row[4],
                        "bidder_cnt": row[5],
                    }
        return result

    # ──────────────────────────────────────────
    # 백테스트 실행
    # ──────────────────────────────────────────

    def _run_backtest(
        self,
        targets: list[tuple[str, str]],
        a_values_map: dict[tuple[str, str], int],
        prelim_map: dict[tuple[str, str], list[int]],
        rank1_map: dict[tuple[str, str], dict],
        verbosity: int,
        strict_sample: bool = False,
        processed_limit: int = 0,
    ) -> dict:
        records = []
        stats = {
            "total_targets": len(targets),
            "processed": 0,
            "processed_limit": processed_limit or None,
            "stopped_by_limit": False,
            "skip_no_a_value": 0,
            "skip_no_prelim": 0,
            "skip_no_rank1": 0,
            "skip_out_of_scope": 0,
            "skip_a_exceeds_est": 0,
            "skip_bid_rate_out_of_range": 0,
            "error": 0,
            "a_incomplete_count": getattr(self, "_a_incomplete_count", 0),
            "strict_sample": strict_sample,
            "strict_prelim_count": STRICT_PRELIM_COUNT if strict_sample else None,
            "strict_bid_rate_min": STRICT_BID_RATE_MIN if strict_sample else None,
            "strict_bid_rate_max": STRICT_BID_RATE_MAX if strict_sample else None,
        }

        table_results = defaultdict(lambda: {
            "count": 0,
            "our_scores": [],
            "rank1_scores": [],
            "gaps": [],
        })

        for i, (ntce_no, ntce_ord) in enumerate(targets, 1):
            if processed_limit and stats["processed"] >= processed_limit:
                stats["stopped_by_limit"] = True
                break

            key = (ntce_no, ntce_ord)

            # A값 확인
            a_value = a_values_map.get(key)
            if a_value is None:
                stats["skip_no_a_value"] += 1
                continue

            # 복수예비가격 확인
            prelim_prices = prelim_map.get(key)
            if not prelim_prices:
                stats["skip_no_prelim"] += 1
                continue

            # 1순위 데이터 확인
            rank1_data = rank1_map.get(key)
            if not rank1_data:
                stats["skip_no_rank1"] += 1
                continue

            presume_price = rank1_data["presume_price"]
            estimated_price = rank1_data["estimated_price"]
            rank1_bid = rank1_data["rank1_bid_amt"]

            # strict-sample: 1순위 bid_rate 필터
            actual_bid_rate = (
                rank1_bid / estimated_price if estimated_price > 0 else 0.0
            )
            if strict_sample:
                if not (
                    STRICT_BID_RATE_MIN <= actual_bid_rate <= STRICT_BID_RATE_MAX
                ):
                    stats["skip_bid_rate_out_of_range"] += 1
                    continue

            # 별표 라우팅 (WorkType=CONSTRUCTION 가정)
            try:
                table_type = select_table(presume_price, WorkType.CONSTRUCTION)
            except ValueError:
                stats["error"] += 1
                continue

            if table_type == TableType.OUT_OF_SCOPE:
                stats["skip_out_of_scope"] += 1
                continue

            # A >= est 체크
            if a_value >= estimated_price:
                stats["skip_a_exceeds_est"] += 1
                continue

            # 최적투찰 엔진 실행
            inp = OptimalBidInput(
                preliminary_prices=prelim_prices,
                a_value=a_value,
                table_type=table_type,
                presume_price=presume_price,
            )

            try:
                opt_result = find_optimal_bid(inp)
            except Exception as e:
                stats["error"] += 1
                if verbosity >= 2:
                    self.stderr.write(f"  오류 {ntce_no}: {e}")
                continue

            stats["processed"] += 1

            # 우리 bid 평가 (실제 예정가격 기준)
            our_eval = evaluate_bid(
                opt_result.recommended_bid, estimated_price,
                a_value, table_type,
            )

            # 1순위 bid 평가
            rank1_eval = evaluate_bid(
                rank1_bid, estimated_price, a_value, table_type,
            )

            gap = round(our_eval.score - rank1_eval.score, 2)

            # ── 신규 지표 ──
            recommended_ratio_pct = (
                opt_result.recommended_bid / estimated_price * 100
            )
            actual_ratio_pct = rank1_bid / estimated_price * 100
            ratio_diff_pp = recommended_ratio_pct - actual_ratio_pct

            band_low_bid = opt_result.band_low
            band_high_bid = opt_result.band_high
            band_low_ratio_pct = (
                band_low_bid / estimated_price * 100 if band_low_bid else 0.0
            )
            band_high_ratio_pct = (
                band_high_bid / estimated_price * 100 if band_high_bid else 0.0
            )
            band_hit = (
                band_low_bid > 0
                and band_high_bid > 0
                and band_low_bid <= rank1_bid <= band_high_bid
            )

            floor_rate_pct = float(get_floor_rate(presume_price))
            # 실제 예정가격 기준 하한 임계값 (사후 검증용)
            # = a + floor_rate% × (estimated_price - a), 올림
            actual_floor_bid = math.ceil(
                a_value + floor_rate_pct / 100.0 * (estimated_price - a_value)
            )
            # 워스트케이스(전 시나리오 통과) 임계값 — engine 산출
            worst_case_floor_bid = opt_result.floor_rate_bid or 0
            floor_pass = opt_result.recommended_bid >= actual_floor_bid

            bidder_cnt = rank1_data.get("bidder_cnt")
            bidder_bucket_actual = _bucket_label(bidder_cnt, BIDDER_BUCKETS)
            amount_bucket = _amount_bucket(estimated_price)

            rec = {
                "bid_ntce_no": ntce_no,
                "bid_ntce_ord": ntce_ord,
                "table_type": table_type.value,
                "presume_price": presume_price,
                "estimated_price": estimated_price,
                "a_value": a_value,
                "n_prelim": len(prelim_prices),
                "n_scenarios": opt_result.n_scenarios,
                "bidder_cnt": bidder_cnt,
                "bidder_bucket_actual": bidder_bucket_actual,
                "bidder_bucket_predicted": None,  # Phase 2 placeholder
                "amount_bucket": amount_bucket,
                "our_bid": opt_result.recommended_bid,
                "our_expected_score": round(opt_result.expected_score, 2),
                "our_actual_score": round(our_eval.score, 2),
                "our_ratio": round(our_eval.ratio, 4),
                "min_scenario_score": round(opt_result.min_scenario_score, 2),
                "max_scenario_score": round(opt_result.max_scenario_score, 2),
                "rank1_bid": rank1_bid,
                "rank1_score": round(rank1_eval.score, 2),
                "gap_vs_rank1": gap,
                # 추천 vs 실제 투찰율 (예정가격 기준 %)
                "recommended_ratio_pct": round(recommended_ratio_pct, 4),
                "actual_ratio_pct": round(actual_ratio_pct, 4),
                "ratio_diff_pp": round(ratio_diff_pp, 4),
                "abs_ratio_error_pp": round(abs(ratio_diff_pp), 4),
                # 밴드 적중
                "band_low_bid": band_low_bid,
                "band_high_bid": band_high_bid,
                "band_low_ratio_pct": round(band_low_ratio_pct, 4),
                "band_high_ratio_pct": round(band_high_ratio_pct, 4),
                "band_hit": band_hit,
                # 하한율 통과 (실제 예정가격 기준 사후 검증)
                "floor_rate_pct": round(floor_rate_pct, 3),
                "actual_floor_bid": actual_floor_bid,
                "worst_case_floor_bid": worst_case_floor_bid,
                "floor_pass": floor_pass,
            }

            table_results[table_type.value]["count"] += 1
            table_results[table_type.value]["our_scores"].append(our_eval.score)
            table_results[table_type.value]["rank1_scores"].append(
                rank1_eval.score
            )
            table_results[table_type.value]["gaps"].append(gap)

            records.append(rec)

            if verbosity >= 2:
                self.stdout.write(
                    f"  [{i}] {ntce_no} "
                    f"our={rec['our_actual_score']:.1f} "
                    f"r1={rec['rank1_score']:.1f} "
                    f"gap={gap:+.1f}"
                )

        return {
            "stats": stats,
            "records": records,
            "table_results": dict(table_results),
        }

    # ──────────────────────────────────────────
    # 리포트 출력
    # ──────────────────────────────────────────

    def _print_summary(self, results: dict):
        s = results["stats"]
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("  DB 기반 최적투찰 백테스트 (BC-35)")
        self.stdout.write("=" * 60)
        self.stdout.write("  ⚠️ WorkType=CONSTRUCTION 가정")
        self.stdout.write("=" * 60)
        self.stdout.write(f"수집 완료 후보:         {s['total_targets']}건")
        self.stdout.write(f"처리 성공:              {s['processed']}건")
        if s.get("stopped_by_limit"):
            self.stdout.write(f"처리 제한 도달:         {s['processed_limit']}건")
        self.stdout.write(f"스킵:")
        self.stdout.write(f"  A값 없음:             {s['skip_no_a_value']}건")
        prelim_skip_label = (
            "복수예비가격 != 15" if s.get("strict_sample")
            else "복수예비가격 < 4"
        )
        self.stdout.write(f"  {prelim_skip_label + ':':<20s} {s['skip_no_prelim']}건")
        self.stdout.write(f"  1순위 데이터 없음:    {s['skip_no_rank1']}건")
        self.stdout.write(f"  OUT_OF_SCOPE:         {s['skip_out_of_scope']}건")
        self.stdout.write(f"  A >= 예정가격:        {s['skip_a_exceeds_est']}건")
        if s.get("strict_sample"):
            self.stdout.write(
                f"  bid_rate 범위 외:     {s['skip_bid_rate_out_of_range']}건 "
                f"(strict-sample, [{s['strict_bid_rate_min']}, "
                f"{s['strict_bid_rate_max']}])"
            )
        self.stdout.write(f"에러:                   {s['error']}건")
        self.stdout.write(f"A값 불완전 (항목<3):    {s['a_incomplete_count']}건")

    def _print_vs_rank1(self, results: dict):
        records = results["records"]

        self.stdout.write("")
        self.stdout.write("[우리 vs 1순위]")
        self.stdout.write(f"대상: {len(records)}건")

        if not records:
            return

        n = len(records)
        wins = sum(1 for r in records if r["gap_vs_rank1"] > 0)
        ties = sum(1 for r in records if r["gap_vs_rank1"] == 0)
        losses = n - wins - ties

        self.stdout.write(
            f"  승 (우리 > 1순위):  {wins:>4d}건 ({wins/n*100:.1f}%)"
        )
        self.stdout.write(
            f"  무 (동일):          {ties:>4d}건 ({ties/n*100:.1f}%)"
        )
        self.stdout.write(
            f"  패 (우리 < 1순위):  {losses:>4d}건 ({losses/n*100:.1f}%)"
        )

        avg_gap = sum(r["gap_vs_rank1"] for r in records) / n
        self.stdout.write(f"  평균 격차: {avg_gap:+.2f}점")

        # 격차 분포
        big_win = sum(1 for r in records if r["gap_vs_rank1"] >= 5)
        small_win = sum(1 for r in records if 0 < r["gap_vs_rank1"] < 5)
        small_loss = sum(1 for r in records if -5 < r["gap_vs_rank1"] < 0)
        big_loss = sum(1 for r in records if r["gap_vs_rank1"] <= -5)
        self.stdout.write(f"\n  격차 분포:")
        self.stdout.write(f"    +5점 이상:  {big_win:>4d}건")
        self.stdout.write(f"    +0~5점:     {small_win:>4d}건")
        self.stdout.write(f"    -5~0점:     {small_loss:>4d}건")
        self.stdout.write(f"    -5점 이하:  {big_loss:>4d}건")

    def _print_prediction_accuracy(self, results: dict):
        records = results["records"]
        has_both = [
            r for r in records
            if "our_expected_score" in r and "our_actual_score" in r
        ]

        self.stdout.write("")
        self.stdout.write("[기대점수 vs 실제점수 (예측력 검증)]")

        if not has_both:
            self.stdout.write("  (데이터 없음)")
            return

        diffs = [
            abs(r["our_expected_score"] - r["our_actual_score"])
            for r in has_both
        ]
        avg_diff = sum(diffs) / len(diffs)
        max_diff = max(diffs)

        self.stdout.write(f"  대상: {len(has_both)}건")
        self.stdout.write(f"  평균 |기대-실제|: {avg_diff:.2f}점")
        self.stdout.write(f"  최대 |기대-실제|: {max_diff:.2f}점")

        n = len(diffs)
        within_1 = sum(1 for d in diffs if d <= 1)
        within_5 = sum(1 for d in diffs if d <= 5)
        within_10 = sum(1 for d in diffs if d <= 10)
        self.stdout.write(f"  1점 이내: {within_1}/{n} ({within_1/n*100:.1f}%)")
        self.stdout.write(f"  5점 이내: {within_5}/{n} ({within_5/n*100:.1f}%)")
        self.stdout.write(
            f"  10점 이내: {within_10}/{n} ({within_10/n*100:.1f}%)"
        )

    # ──────────────────────────────────────────
    # 신규 리포트 (백테스트 지표 확장)
    # ──────────────────────────────────────────

    def _print_bid_rate_comparison(self, results: dict):
        records = results["records"]
        self.stdout.write("")
        self.stdout.write("[추천 투찰율 vs 실제 1순위 투찰율 (예정가격 기준 %)]")
        self.stdout.write(f"대상: {len(records)}건")

        if not records:
            return

        n = len(records)
        recs_pct = [r["recommended_ratio_pct"] for r in records]
        acts_pct = [r["actual_ratio_pct"] for r in records]
        diffs = [r["ratio_diff_pp"] for r in records]
        abs_diffs = [r["abs_ratio_error_pp"] for r in records]

        avg_rec = sum(recs_pct) / n
        avg_act = sum(acts_pct) / n
        avg_diff = sum(diffs) / n
        avg_abs = sum(abs_diffs) / n
        max_abs = max(abs_diffs)
        med_abs = sorted(abs_diffs)[n // 2]

        self.stdout.write(f"  평균 추천 투찰율:  {avg_rec:.3f}%")
        self.stdout.write(f"  평균 실제 투찰율:  {avg_act:.3f}%")
        self.stdout.write(
            f"  평균 차이 (rec-act): {avg_diff:+.3f}%p  "
            f"(>0 = 추천이 더 높음)"
        )
        self.stdout.write(
            f"  평균 |오차|: {avg_abs:.3f}%p / 중앙값: {med_abs:.3f}%p / "
            f"최대: {max_abs:.3f}%p"
        )

        for thr in (0.5, 1.0, 2.0, 5.0):
            within = sum(1 for d in abs_diffs if d <= thr)
            self.stdout.write(
                f"  |오차| <= {thr:.1f}%p: {within}/{n} ({within / n * 100:.1f}%)"
            )

        # 부호별 분포
        over = sum(1 for d in diffs if d > 0)
        under = sum(1 for d in diffs if d < 0)
        equal = n - over - under
        self.stdout.write(
            f"  추천 > 실제 (과대추천): {over}건 ({over / n * 100:.1f}%)"
        )
        self.stdout.write(
            f"  추천 < 실제 (과소추천): {under}건 ({under / n * 100:.1f}%)"
        )
        self.stdout.write(f"  동일:                  {equal}건")

    def _print_band_hit(self, results: dict):
        records = results["records"]
        self.stdout.write("")
        self.stdout.write("[밴드 적중 — 추천 [band_low, band_high] 안에 1순위 bid 포함 여부]")
        self.stdout.write(f"대상: {len(records)}건")

        if not records:
            return

        n = len(records)
        hit = sum(1 for r in records if r["band_hit"])
        self.stdout.write(
            f"  적중: {hit}/{n} ({hit / n * 100:.2f}%)"
        )

        # 평균 밴드 폭 (%p, 예정가격 기준)
        widths = [
            r["band_high_ratio_pct"] - r["band_low_ratio_pct"]
            for r in records
        ]
        if widths:
            avg_w = sum(widths) / len(widths)
            self.stdout.write(f"  평균 밴드 폭: {avg_w:.3f}%p")

    def _print_floor_pass(self, results: dict):
        records = results["records"]
        self.stdout.write("")
        self.stdout.write("[하한율 통과 — 추천 bid >= 실제 예정가격 기준 하한]")
        self.stdout.write(f"대상: {len(records)}건")

        if not records:
            return

        n = len(records)
        passed = sum(1 for r in records if r["floor_pass"])
        self.stdout.write(
            f"  통과: {passed}/{n} ({passed / n * 100:.2f}%)"
        )
        failed = n - passed
        if failed:
            self.stdout.write(self.style.WARNING(
                f"  미통과: {failed}건 — 하한율 미달 위험"
            ))

    def _print_by_amount_bucket(self, results: dict):
        records = results["records"]
        self.stdout.write("")
        self.stdout.write("[금액대별 요약]")

        if not records:
            return

        bucket_labels = [label for _, _, label in AMOUNT_BUCKETS]
        groups: dict[str, list[dict]] = {label: [] for label in bucket_labels}
        for r in records:
            groups.setdefault(r["amount_bucket"], []).append(r)

        self.stdout.write(
            f"{'금액대':<10s} {'건수':>5s} {'평균오차(%p)':>13s} "
            f"{'밴드적중률':>10s} {'하한통과율':>10s}"
        )
        for label in bucket_labels:
            grp = groups.get(label, [])
            if not grp:
                continue
            n = len(grp)
            avg_abs = sum(r["abs_ratio_error_pp"] for r in grp) / n
            hit_rate = sum(1 for r in grp if r["band_hit"]) / n * 100
            pass_rate = sum(1 for r in grp if r["floor_pass"]) / n * 100
            self.stdout.write(
                f"{label:<10s} {n:>5d} {avg_abs:>13.3f} "
                f"{hit_rate:>9.1f}% {pass_rate:>9.1f}%"
            )

    def _print_by_bidder_bucket(self, results: dict):
        records = results["records"]
        self.stdout.write("")
        self.stdout.write("[투찰자수 구간별 요약]")

        if not records:
            return

        bucket_labels = [label for _, _, label in BIDDER_BUCKETS] + ["unknown"]
        groups: dict[str, list[dict]] = {label: [] for label in bucket_labels}
        for r in records:
            groups.setdefault(r["bidder_bucket_actual"], []).append(r)

        self.stdout.write(
            f"{'투찰자':<10s} {'건수':>5s} {'평균오차(%p)':>13s} "
            f"{'밴드적중률':>10s} {'평균실제투찰율':>14s}"
        )
        for label in bucket_labels:
            grp = groups.get(label, [])
            if not grp:
                continue
            n = len(grp)
            avg_abs = sum(r["abs_ratio_error_pp"] for r in grp) / n
            hit_rate = sum(1 for r in grp if r["band_hit"]) / n * 100
            avg_act = sum(r["actual_ratio_pct"] for r in grp) / n
            self.stdout.write(
                f"{label:<10s} {n:>5d} {avg_abs:>13.3f} "
                f"{hit_rate:>9.1f}% {avg_act:>13.3f}%"
            )

    def _print_by_table(self, results: dict):
        table_results = results["table_results"]

        self.stdout.write("")
        self.stdout.write("[별표별 분석]")
        self.stdout.write(
            f"{'별표':<12s} {'건수':>4s} {'우리평균':>8s} "
            f"{'1순위평균':>10s} {'격차':>8s}"
        )

        for table in sorted(table_results.keys()):
            tr = table_results[table]
            n = tr["count"]
            our_avg = sum(tr["our_scores"]) / n if n else 0

            rank1_avg = "-"
            if tr["rank1_scores"]:
                rank1_avg = f"{sum(tr['rank1_scores'])/len(tr['rank1_scores']):.1f}"

            gap_avg = "-"
            if tr["gaps"]:
                gap_avg = f"{sum(tr['gaps'])/len(tr['gaps']):+.1f}"

            self.stdout.write(
                f"{table:<12s} {n:>4d} {our_avg:>8.1f} "
                f"{rank1_avg:>10s} {gap_avg:>8s}"
            )

    # ──────────────────────────────────────────
    # JSON 요약 빌더
    # ──────────────────────────────────────────

    def _build_bid_rate_summary(self, records: list[dict]) -> dict:
        if not records:
            return {}
        n = len(records)
        diffs = [r["ratio_diff_pp"] for r in records]
        abs_diffs = [r["abs_ratio_error_pp"] for r in records]
        rec_pct = [r["recommended_ratio_pct"] for r in records]
        act_pct = [r["actual_ratio_pct"] for r in records]
        sorted_abs = sorted(abs_diffs)
        return {
            "total": n,
            "avg_recommended_pct": round(sum(rec_pct) / n, 4),
            "avg_actual_pct": round(sum(act_pct) / n, 4),
            "avg_diff_pp": round(sum(diffs) / n, 4),
            "avg_abs_error_pp": round(sum(abs_diffs) / n, 4),
            "median_abs_error_pp": round(sorted_abs[n // 2], 4),
            "max_abs_error_pp": round(max(abs_diffs), 4),
            "within_0_5pp": sum(1 for d in abs_diffs if d <= 0.5),
            "within_1pp": sum(1 for d in abs_diffs if d <= 1.0),
            "within_2pp": sum(1 for d in abs_diffs if d <= 2.0),
            "within_5pp": sum(1 for d in abs_diffs if d <= 5.0),
            "over_recommend": sum(1 for d in diffs if d > 0),
            "under_recommend": sum(1 for d in diffs if d < 0),
            "equal": sum(1 for d in diffs if d == 0),
        }

    def _build_band_summary(self, records: list[dict]) -> dict:
        if not records:
            return {}
        n = len(records)
        hit = sum(1 for r in records if r["band_hit"])
        widths = [
            r["band_high_ratio_pct"] - r["band_low_ratio_pct"]
            for r in records
        ]
        return {
            "total": n,
            "hit": hit,
            "hit_rate": round(hit / n, 4),
            "avg_band_width_pp": round(sum(widths) / len(widths), 4),
        }

    def _build_floor_summary(self, records: list[dict]) -> dict:
        if not records:
            return {}
        n = len(records)
        passed = sum(1 for r in records if r["floor_pass"])
        return {
            "total": n,
            "passed": passed,
            "failed": n - passed,
            "pass_rate": round(passed / n, 4),
        }

    def _build_bucket_summary(
        self,
        records: list[dict],
        bucket_field: str,
        bucket_order: list[str],
    ) -> dict:
        if not records:
            return {}
        groups: dict[str, list[dict]] = {label: [] for label in bucket_order}
        for r in records:
            groups.setdefault(r[bucket_field], []).append(r)

        out = {}
        for label in bucket_order:
            grp = groups.get(label, [])
            if not grp:
                continue
            n = len(grp)
            out[label] = {
                "count": n,
                "avg_abs_error_pp": round(
                    sum(r["abs_ratio_error_pp"] for r in grp) / n, 4
                ),
                "band_hit_rate": round(
                    sum(1 for r in grp if r["band_hit"]) / n, 4
                ),
                "floor_pass_rate": round(
                    sum(1 for r in grp if r["floor_pass"]) / n, 4
                ),
                "avg_recommended_pct": round(
                    sum(r["recommended_ratio_pct"] for r in grp) / n, 4
                ),
                "avg_actual_pct": round(
                    sum(r["actual_ratio_pct"] for r in grp) / n, 4
                ),
            }
        return out

    # ──────────────────────────────────────────
    # JSON 저장
    # ──────────────────────────────────────────

    def _save_json(self, results: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path

        path.parent.mkdir(parents=True, exist_ok=True)

        # 별표별 요약
        by_table = {}
        for table, tr in results["table_results"].items():
            n = tr["count"]
            entry = {"count": n}
            if tr["our_scores"]:
                entry["our_avg_score"] = round(
                    sum(tr["our_scores"]) / len(tr["our_scores"]), 2
                )
            if tr["rank1_scores"]:
                entry["rank1_avg_score"] = round(
                    sum(tr["rank1_scores"]) / len(tr["rank1_scores"]), 2
                )
            if tr["gaps"]:
                entry["avg_gap_vs_rank1"] = round(
                    sum(tr["gaps"]) / len(tr["gaps"]), 2
                )
            by_table[table] = entry

        # vs 1순위 요약
        records = results["records"]
        comparison_rank1 = {}
        if records:
            n = len(records)
            comparison_rank1 = {
                "total": n,
                "wins": sum(1 for r in records if r["gap_vs_rank1"] > 0),
                "ties": sum(1 for r in records if r["gap_vs_rank1"] == 0),
                "losses": sum(1 for r in records if r["gap_vs_rank1"] < 0),
                "avg_gap": round(
                    sum(r["gap_vs_rank1"] for r in records) / n, 2
                ),
            }

        # 예측력
        has_pred = [
            r for r in records
            if "our_expected_score" in r and "our_actual_score" in r
        ]
        prediction = {}
        if has_pred:
            diffs = [
                abs(r["our_expected_score"] - r["our_actual_score"])
                for r in has_pred
            ]
            n = len(diffs)
            prediction = {
                "total": n,
                "avg_diff": round(sum(diffs) / n, 2),
                "max_diff": round(max(diffs), 2),
                "within_1pt": sum(1 for d in diffs if d <= 1),
                "within_5pt": sum(1 for d in diffs if d <= 5),
                "within_10pt": sum(1 for d in diffs if d <= 10),
            }

        bid_rate_summary = self._build_bid_rate_summary(records)
        band_summary = self._build_band_summary(records)
        floor_summary = self._build_floor_summary(records)
        amount_summary = self._build_bucket_summary(
            records, "amount_bucket",
            [label for _, _, label in AMOUNT_BUCKETS],
        )
        bidder_summary = self._build_bucket_summary(
            records, "bidder_bucket_actual",
            [label for _, _, label in BIDDER_BUCKETS] + ["unknown"],
        )

        report = {
            "meta": {
                "command": "simulate_optimal_bid_db",
                "bc_id": "BC-35",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "description": "DB 기반 최적투찰 백테스트",
                "warning": "WorkType=CONSTRUCTION 가정",
                "strict_sample": getattr(self, "_strict_sample", False),
                "strict_prelim_count": (
                    STRICT_PRELIM_COUNT
                    if getattr(self, "_strict_sample", False) else None
                ),
                "strict_bid_rate_min": (
                    STRICT_BID_RATE_MIN
                    if getattr(self, "_strict_sample", False) else None
                ),
                "strict_bid_rate_max": (
                    STRICT_BID_RATE_MAX
                    if getattr(self, "_strict_sample", False) else None
                ),
                "processed_limit": results["stats"].get("processed_limit"),
            },
            "stats": results["stats"],
            "comparison_vs_rank1": comparison_rank1,
            "prediction_accuracy": prediction,
            "bid_rate_comparison": bid_rate_summary,
            "band_hit": band_summary,
            "floor_pass": floor_summary,
            "by_table": by_table,
            "by_amount_bucket": amount_summary,
            "by_bidder_bucket": bidder_summary,
            "records": records,
        }

        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"JSON 저장: {path}"))
