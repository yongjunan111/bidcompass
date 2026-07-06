"""시장 기반 사전추천 A/B 백테스트 (Stage D).

모델 A: prebid_recommend 기본 모드 (90% 계산식)
모델 B: as-of 경쟁강도 추정 → get_market_policy → market_center 주입
        (policy 폴백 시 모델 A와 동일 값 사용, 폴백으로 카운트)

지표 이원화:
  - market-fit: 실현 예정가격 기준 추천율 vs 실제 1순위 투찰율
    (MAE/중앙값 오차 %p, 과대추천 비율, 실전 하한율 통과율)
  - 엔진 일치성: serving 기준 하한 통과율(구조상 100%여야 함, 검증용),
    순공사원가 98% 통과율(추정 threshold 기준 — 추정치임에 유의)

한계 (해석 시 유의):
  - segment_policy_v1.json은 전 기간 산출물 → in-sample 비교
    (as-of 처리는 경쟁강도 추정에만 적용됨)
  - 순공사원가 threshold는 estimate_net_construction_cost 추정값

⚠️ DB는 SELECT 전용. 어떤 테이블에도 쓰지 않는다.

사용:
    python manage.py backtest_prebid --limit 20
    python manage.py backtest_prebid --limit 200 --output data/collected/backtest_prebid_ab.json
"""

import calendar
import json
import math
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from g2b.models import (
    BidAnnouncement,
    BidApiAValue,
    BidApiCollectionLog,
    BidApiPrelimPrice,
)
from g2b.services.bid_engine import (
    AValueItems,
    TableType,
    WorkType,
    calculate_a_value,
    get_floor_rate,
    select_table,
)
from g2b.services.market_policy import _comp_seg, get_market_policy
from g2b.services.prebid_recommend import prebid_recommend
from g2b.ui_api import _infer_work_type

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

QUERY_BATCH_SIZE = 1000

# as-of 경쟁강도 추정 윈도우 (report_stats.get_similar_bid_stats와 동일 정신)
ASOF_PRIMARY = (0.15, 24)    # ±15%, 24개월
ASOF_EXPANDED = (0.25, 36)   # ±25%, 36개월
ASOF_MIN_COUNT = 30

_DATE8_RE = re.compile(r"^\d{8}$")

# TableType → price_seg 라벨 (리포트용; TABLE_2B는 정책 없음 → 항상 폴백)
_PRICE_SEG_LABELS = {
    TableType.TABLE_1: "T1",
    TableType.TABLE_2A: "T2A",
    TableType.TABLE_2B: "T2B",
    TableType.TABLE_3: "T3",
    TableType.TABLE_4: "T4",
    TableType.TABLE_5: "T5",
}


def _shift_months(yyyymmdd: str, months: int) -> str:
    """YYYYMMDD 문자열에서 months개월 이전 날짜 (일자는 월말로 클램프)."""
    year = int(yyyymmdd[0:4])
    month = int(yyyymmdd[4:6])
    day = int(yyyymmdd[6:8])
    total = year * 12 + (month - 1) - months
    new_year, new_month0 = divmod(total, 12)
    new_month = new_month0 + 1
    last_day = calendar.monthrange(new_year, new_month)[1]
    return f"{new_year:04d}{new_month:02d}{min(day, last_day):02d}"


def _bidder_seg_label(bidder_cnt) -> str:
    """실현 참가자수 → 경쟁강도 버킷 라벨 (market_policy와 동일 경계)."""
    if bidder_cnt is None:
        return "unknown"
    return _comp_seg(float(bidder_cnt)) or "unknown"


class Command(BaseCommand):
    help = "시장 기반 사전추천 A/B 백테스트 (모델 A=90% 기본 vs 모델 B=시장 주입)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=200,
            help="처리 후보 건수 제한 (0=전체, 기본 200)",
        )
        parser.add_argument(
            "--offset", type=int, default=0,
            help="후보 목록 시작 오프셋 (기본 0)",
        )
        parser.add_argument(
            "--output", type=str,
            default="data/collected/backtest_prebid_ab.json",
            help="JSON 결과 저장 경로",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        offset = options["offset"]
        output_path = options["output"]
        verbosity = options["verbosity"]
        started = time.monotonic()

        # 1. 대상 공고 추출 (A값+복수예비가격 수집 완료)
        self.stdout.write("수집 완료 공고 목록 조회 중...")
        targets = self._get_targets(limit, offset)
        self.stdout.write(f"  백테스트 후보: {len(targets)}건 (offset={offset})")
        if not targets:
            self.stdout.write(self.style.WARNING("대상 없음"))
            return

        # 2. 데이터 로드 (전부 SELECT)
        self.stdout.write("A값/기초금액/1순위/개찰일 데이터 로드 중...")
        a_values_map = self._load_a_values(targets)
        base_amount_map = self._load_base_amounts(targets)
        rank1_map = self._load_rank1_data(targets)
        openg_map = self._load_openg_dates(targets)
        announcement_map = self._load_announcements(targets)
        self.stdout.write(
            f"  A값: {len(a_values_map)}건, 기초금액: {len(base_amount_map)}건, "
            f"1순위: {len(rank1_map)}건, 개찰일: {len(openg_map)}건"
        )

        # 3. A/B 백테스트 실행
        results = self._run_backtest(
            targets, a_values_map, base_amount_map, rank1_map,
            openg_map, announcement_map, verbosity,
        )
        results["meta"] = {
            "command": "backtest_prebid",
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "limit": limit,
            "offset": offset,
            "duration_sec": round(time.monotonic() - started, 1),
            "caveats": [
                "segment_policy_v1.json은 전 기간 산출물 — in-sample 비교 "
                "(as-of 처리는 경쟁강도 추정에만 적용)",
                "순공사원가 98% threshold는 estimate_net_construction_cost 추정값",
                "예정가격≈기초금액 근사 (serving과 동일)",
            ],
        }

        # 4. 요약 출력 + JSON 저장
        self._print_report(results)
        self._save_json(results, output_path)

    # ──────────────────────────────────────────
    # 데이터 로드 (SELECT 전용)
    # ──────────────────────────────────────────

    def _get_targets(self, limit: int, offset: int) -> list[tuple[str, str]]:
        """A값 + 복수예비가격 둘 다 수집 완료된 공고 목록."""
        qs = (
            BidApiCollectionLog.objects
            .filter(a_value_status="ok", prelim_status="ok")
            .values_list("bid_ntce_no", "bid_ntce_ord")
            .order_by("-bid_ntce_no")
        )
        if limit > 0:
            return list(qs[offset:offset + limit])
        return list(qs[offset:])

    def _load_a_values(
        self, targets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], int]:
        """A값 DB → {(ntce_no, ntce_ord): a_value_int}."""
        result = {}
        for ntce_no, ntce_ord in targets:
            try:
                row = BidApiAValue.objects.get(
                    bid_ntce_no=ntce_no, bid_ntce_ord=ntce_ord,
                )
            except BidApiAValue.DoesNotExist:
                continue
            items = AValueItems(
                national_pension=row.national_pension,
                health_insurance=row.health_insurance,
                retirement_mutual_aid=row.retirement_mutual_aid,
                long_term_care=row.long_term_care,
                occupational_safety=row.occupational_safety,
                safety_management=row.safety_management,
                quality_management=row.quality_management,
            )
            result[(ntce_no, ntce_ord)] = calculate_a_value(items)
        return result

    def _load_base_amounts(
        self, targets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], int]:
        """복수예비가격 테이블의 기초금액 → {(ntce_no, ntce_ord): base_amount}."""
        result = {}
        for ntce_no, ntce_ord in targets:
            base_amount = (
                BidApiPrelimPrice.objects
                .filter(
                    bid_ntce_no=ntce_no,
                    bid_ntce_ord=ntce_ord,
                    base_amount__gt=0,
                )
                .order_by("sequence_no")
                .values_list("base_amount", flat=True)
                .first()
            )
            if base_amount:
                result[(ntce_no, ntce_ord)] = base_amount
        return result

    def _load_rank1_data(
        self, targets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], dict]:
        """1순위(낙찰자) 데이터 로드. openg_rank='1', 공고당 1건."""
        if not targets:
            return {}

        result = {}
        with connection.cursor() as cursor:
            for start in range(0, len(targets), QUERY_BATCH_SIZE):
                batch = targets[start:start + QUERY_BATCH_SIZE]
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
                      AND bid_amt > 0
                      AND openg_rank = '1'
                    ORDER BY bid_ntce_no, bid_ntce_ord, bid_amt ASC
                """
                cursor.execute(sql, flat_params)
                for row in cursor.fetchall():
                    result[(row[0], row[1])] = {
                        "presume_price": row[2],
                        "estimated_price": row[3],
                        "rank1_bid_amt": row[4],
                        "bidder_cnt": row[5],
                    }
        return result

    def _load_openg_dates(
        self, targets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], str]:
        """BidContract 개찰일자(YYYYMMDD) → {(ntce_no, ntce_ord): openg_date}."""
        if not targets:
            return {}

        result = {}
        with connection.cursor() as cursor:
            for start in range(0, len(targets), QUERY_BATCH_SIZE):
                batch = targets[start:start + QUERY_BATCH_SIZE]
                placeholders = ", ".join(["(%s, %s)"] * len(batch))
                flat_params = []
                for ntce_no, ntce_ord in batch:
                    flat_params.extend([ntce_no, ntce_ord])

                sql = f"""
                    SELECT DISTINCT ON (bid_ntce_no, bid_ntce_ord)
                        bid_ntce_no, bid_ntce_ord, openg_date
                    FROM g2b_bidcontract
                    WHERE (bid_ntce_no, bid_ntce_ord) IN ({placeholders})
                      AND openg_date ~ '^[0-9]{{8}}$'
                    ORDER BY bid_ntce_no, bid_ntce_ord, openg_date ASC
                """
                cursor.execute(sql, flat_params)
                for row in cursor.fetchall():
                    result[(row[0], row[1])] = row[2]
        return result

    def _load_announcements(
        self, targets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], BidAnnouncement]:
        """work_type 추론용 공고 텍스트 로드 (없으면 CONSTRUCTION 폴백)."""
        if not targets:
            return {}
        ntce_nos = list({ntce_no for ntce_no, _ in targets})
        result = {}
        qs = (
            BidAnnouncement.objects
            .filter(bid_ntce_no__in=ntce_nos)
            .only("bid_ntce_no", "bid_ntce_ord", "license_limit_list", "bid_ntce_nm")
        )
        for ann in qs:
            result[(ann.bid_ntce_no, ann.bid_ntce_ord)] = ann
        return result

    # ──────────────────────────────────────────
    # as-of 경쟁강도 추정 (누수 제거: 개찰일 이전 데이터만)
    # ──────────────────────────────────────────

    def _query_asof(
        self, presume_price: int, asof: str, pct: float, months: int,
    ):
        """asof(YYYYMMDD) 이전 [asof−months, asof) 윈도우의 유사 공고
        1순위 평균 참가자수. 실패 시 None, 성공 시 (count, avg)."""
        lower = int(presume_price * (1 - pct))
        upper = int(presume_price * (1 + pct))
        since = _shift_months(asof, months)

        sql = """
            WITH rank1 AS (
                SELECT DISTINCT ON (br.bid_ntce_no, br.bid_ntce_ord)
                    br.bidder_cnt
                FROM g2b_bidresult br
                JOIN g2b_bidcontract bc
                    ON br.bid_ntce_no = bc.bid_ntce_no
                    AND br.bid_ntce_ord = bc.bid_ntce_ord
                WHERE bc.presume_price BETWEEN %s AND %s
                  AND br.openg_rank = '1'
                  AND bc.openg_date >= %s
                  AND bc.openg_date < %s
                ORDER BY br.bid_ntce_no, br.bid_ntce_ord
            )
            SELECT COUNT(*), COALESCE(AVG(bidder_cnt), 0) FROM rank1
        """
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = '5s'")
                cursor.execute(sql, [lower, upper, since, asof])
                row = cursor.fetchone()
        except Exception as exc:
            self._asof_error_count += 1
            if self._verbosity >= 2:
                self.stderr.write(f"  as-of 쿼리 실패 (asof={asof}): {exc}")
            return None
        if not row:
            return None
        return int(row[0]), float(row[1])

    def _asof_avg_bidder_cnt(self, presume_price: int, asof: str):
        """as-of 평균 참가자수. (avg, count, window_label) — 데이터 없으면 (None, 0, '')."""
        pct, months = ASOF_PRIMARY
        res = self._query_asof(presume_price, asof, pct, months)
        if res is not None and res[0] >= ASOF_MIN_COUNT:
            return res[1], res[0], f"±{int(pct * 100)}%/{months}mo"

        pct, months = ASOF_EXPANDED
        res = self._query_asof(presume_price, asof, pct, months)
        if res is None or res[0] == 0:
            return None, 0, ""
        return res[1], res[0], f"±{int(pct * 100)}%/{months}mo"

    # ──────────────────────────────────────────
    # 백테스트 실행
    # ──────────────────────────────────────────

    def _run_backtest(
        self,
        targets: list[tuple[str, str]],
        a_values_map: dict,
        base_amount_map: dict,
        rank1_map: dict,
        openg_map: dict,
        announcement_map: dict,
        verbosity: int,
    ) -> dict:
        self._verbosity = verbosity
        self._asof_error_count = 0

        records = []
        stats = {
            "total_targets": len(targets),
            "processed": 0,
            "skip_no_a_value": 0,
            "skip_no_base_amount": 0,
            "skip_no_rank1": 0,
            "skip_no_openg_date": 0,
            "skip_out_of_scope": 0,
            "skip_a_exceeds_est": 0,
            "error": 0,
            "b_applied": 0,
            "b_fallback_no_asof": 0,
            "b_fallback_policy_gate": 0,
            "asof_query_error": 0,
        }

        for i, (ntce_no, ntce_ord) in enumerate(targets, 1):
            key = (ntce_no, ntce_ord)

            a_value = a_values_map.get(key)
            if a_value is None:
                stats["skip_no_a_value"] += 1
                continue

            base_amount = base_amount_map.get(key)
            if not base_amount:
                stats["skip_no_base_amount"] += 1
                continue

            rank1 = rank1_map.get(key)
            if not rank1:
                stats["skip_no_rank1"] += 1
                continue

            asof = openg_map.get(key)
            if not asof or not _DATE8_RE.match(asof):
                stats["skip_no_openg_date"] += 1
                continue

            presume_price = rank1["presume_price"]
            estimated_price = rank1["estimated_price"]
            rank1_bid = rank1["rank1_bid_amt"]
            bidder_cnt = rank1["bidder_cnt"]

            # 별표 라우팅 (공고 텍스트 기반 work_type 추론, 없으면 CONSTRUCTION)
            work_type = _infer_work_type(announcement_map.get(key))
            try:
                table_type = select_table(presume_price, work_type)
            except ValueError:
                stats["error"] += 1
                continue
            if table_type == TableType.OUT_OF_SCOPE:
                stats["skip_out_of_scope"] += 1
                continue

            # 엔진 전제조건: A < 기초금액, A < 실현 예정가격
            if a_value >= base_amount or a_value >= estimated_price:
                stats["skip_a_exceeds_est"] += 1
                continue

            # ── 모델 A: 기본(90%) 추천 ──
            try:
                res_a = prebid_recommend(
                    base_amount, a_value, table_type, presume_price,
                )
            except Exception as exc:
                stats["error"] += 1
                if verbosity >= 2:
                    self.stderr.write(f"  오류 {ntce_no} (모델 A): {exc}")
                continue

            # ── 모델 B: as-of 경쟁강도 → 정책 → market 주입 ──
            asof_avg, asof_cnt, asof_window = self._asof_avg_bidder_cnt(
                presume_price, asof,
            )
            policy = get_market_policy(table_type, asof_avg, presume_price)
            if policy is not None:
                try:
                    res_b = prebid_recommend(
                        base_amount, a_value, table_type, presume_price,
                        market_center=policy.center,
                        market_segment=policy.segment_id,
                    )
                except Exception as exc:
                    stats["error"] += 1
                    if verbosity >= 2:
                        self.stderr.write(f"  오류 {ntce_no} (모델 B): {exc}")
                    continue
                b_applied = True
                b_fallback_reason = ""
                stats["b_applied"] += 1
            else:
                res_b = res_a  # 폴백: 모델 A와 동일
                b_applied = False
                if asof_avg is None:
                    b_fallback_reason = "no_asof_competition"
                    stats["b_fallback_no_asof"] += 1
                else:
                    b_fallback_reason = "policy_gate"
                    stats["b_fallback_policy_gate"] += 1

            stats["processed"] += 1

            # ── 공통 기준값 ──
            floor_rate_pct = float(get_floor_rate(presume_price))
            # 실전 하한 (실현 예정가격 기준 사후 검증)
            realized_floor_bid = math.ceil(
                a_value + floor_rate_pct / 100.0 * (estimated_price - a_value)
            )
            rank1_rate = rank1_bid / estimated_price * 100

            rec = {
                "bid_ntce_no": ntce_no,
                "bid_ntce_ord": ntce_ord,
                "table_type": table_type.value,
                "price_seg": _PRICE_SEG_LABELS.get(table_type, "unknown"),
                "work_type": work_type.value,
                "presume_price": presume_price,
                "base_amount": base_amount,
                "estimated_price": estimated_price,
                "a_value": a_value,
                "asof_date": asof,
                "asof_avg_bidder": (
                    round(asof_avg, 2) if asof_avg is not None else None
                ),
                "asof_sample_n": asof_cnt,
                "asof_window": asof_window,
                "bidder_cnt": bidder_cnt,
                "bidder_seg": _bidder_seg_label(bidder_cnt),
                "rank1_bid": rank1_bid,
                "rank1_rate_pct": round(rank1_rate, 4),
                "floor_rate_pct": round(floor_rate_pct, 3),
                "realized_floor_bid": realized_floor_bid,
                "net_cost_threshold_estimated": res_a.net_cost_threshold,
                "b_applied": b_applied,
                "b_fallback_reason": b_fallback_reason,
                "market_segment": policy.segment_id if policy else "",
                "market_center": policy.center if policy else None,
            }
            rec.update(self._model_fields(
                "a", res_a, estimated_price, rank1_rate, realized_floor_bid,
            ))
            rec.update(self._model_fields(
                "b", res_b, estimated_price, rank1_rate, realized_floor_bid,
            ))
            records.append(rec)

            if verbosity >= 2:
                self.stdout.write(
                    f"  [{i}] {ntce_no} A={rec['rate_a_pct']:.3f}% "
                    f"B={rec['rate_b_pct']:.3f}% 실제={rank1_rate:.3f}% "
                    f"({'B적용' if b_applied else '폴백'})"
                )

        stats["asof_query_error"] = self._asof_error_count
        return {"stats": stats, "records": records}

    @staticmethod
    def _model_fields(
        suffix: str,
        result,
        estimated_price: int,
        rank1_rate: float,
        realized_floor_bid: int,
    ) -> dict:
        """모델별 지표 필드 (market-fit + 엔진 일치성)."""
        bid = result.optimal_bid
        rate = bid / estimated_price * 100
        err = rate - rank1_rate
        return {
            f"bid_{suffix}": bid,
            f"rate_{suffix}_pct": round(rate, 4),
            f"err_{suffix}_pp": round(err, 4),
            f"abs_err_{suffix}_pp": round(abs(err), 4),
            f"over_{suffix}": err > 0,
            # market-fit: 실현 예정가격 기준 하한 통과
            f"realized_floor_pass_{suffix}": bid >= realized_floor_bid,
            # 엔진 일치성: serving 기준 하한 통과 (구조상 100%여야 함)
            f"serving_floor_pass_{suffix}": result.floor_rate_pass,
            # 엔진 일치성: 순공사원가 98% 통과 (추정 threshold)
            f"net_cost_pass_{suffix}": result.net_cost_pass,
            f"score_{suffix}": round(float(result.optimal_score), 2),
        }

    # ──────────────────────────────────────────
    # 요약 빌더
    # ──────────────────────────────────────────

    @staticmethod
    def _model_summary(records: list[dict], suffix: str) -> dict:
        if not records:
            return {}
        n = len(records)
        abs_errs = sorted(r[f"abs_err_{suffix}_pp"] for r in records)
        errs = [r[f"err_{suffix}_pp"] for r in records]
        return {
            "n": n,
            "mae_pp": round(sum(abs_errs) / n, 4),
            "median_abs_err_pp": round(abs_errs[n // 2], 4),
            "avg_err_pp": round(sum(errs) / n, 4),
            "over_recommend_rate": round(
                sum(1 for r in records if r[f"over_{suffix}"]) / n, 4
            ),
            "realized_floor_pass_rate": round(
                sum(1 for r in records if r[f"realized_floor_pass_{suffix}"]) / n, 4
            ),
            "serving_floor_pass_rate": round(
                sum(1 for r in records if r[f"serving_floor_pass_{suffix}"]) / n, 4
            ),
            "net_cost_pass_rate_estimated": round(
                sum(1 for r in records if r[f"net_cost_pass_{suffix}"]) / n, 4
            ),
        }

    def _segment_summary(self, records: list[dict]) -> dict:
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in records:
            groups[f"{r['price_seg']}|{r['bidder_seg']}"].append(r)

        out = {}
        for seg_key in sorted(groups.keys()):
            grp = groups[seg_key]
            n = len(grp)
            mae_a = sum(r["abs_err_a_pp"] for r in grp) / n
            mae_b = sum(r["abs_err_b_pp"] for r in grp) / n
            out[seg_key] = {
                "n": n,
                "mae_a_pp": round(mae_a, 4),
                "mae_b_pp": round(mae_b, 4),
                "delta_mae_pp": round(mae_b - mae_a, 4),
                "b_applied": sum(1 for r in grp if r["b_applied"]),
                "b_fallback": sum(1 for r in grp if not r["b_applied"]),
            }
        return out

    # ──────────────────────────────────────────
    # 리포트 출력
    # ──────────────────────────────────────────

    def _print_report(self, results: dict):
        s = results["stats"]
        records = results["records"]

        self.stdout.write("")
        self.stdout.write("=" * 64)
        self.stdout.write("  시장 기반 사전추천 A/B 백테스트 (backtest_prebid)")
        self.stdout.write("=" * 64)
        self.stdout.write("  모델 A: 90% 기본 / 모델 B: as-of 경쟁강도 → 시장 주입")
        self.stdout.write("  ⚠️ policy는 전 기간 산출물(in-sample), 순공사원가는 추정 threshold")
        self.stdout.write("=" * 64)
        self.stdout.write(f"후보:                   {s['total_targets']}건")
        self.stdout.write(f"처리 성공:              {s['processed']}건")
        self.stdout.write("스킵:")
        self.stdout.write(f"  A값 없음:             {s['skip_no_a_value']}건")
        self.stdout.write(f"  기초금액 없음:        {s['skip_no_base_amount']}건")
        self.stdout.write(f"  1순위 데이터 없음:    {s['skip_no_rank1']}건")
        self.stdout.write(f"  개찰일(openg_date) 없음: {s['skip_no_openg_date']}건")
        self.stdout.write(f"  OUT_OF_SCOPE:         {s['skip_out_of_scope']}건")
        self.stdout.write(f"  A >= 기초/예정가격:   {s['skip_a_exceeds_est']}건")
        self.stdout.write(f"에러:                   {s['error']}건")
        self.stdout.write(f"as-of 쿼리 실패:        {s['asof_query_error']}건")

        if not records:
            self.stdout.write(self.style.WARNING("처리된 레코드 없음"))
            return

        n = len(records)
        self.stdout.write("")
        self.stdout.write("[모델 B 적용 현황]")
        self.stdout.write(
            f"  B 적용: {s['b_applied']}건 ({s['b_applied'] / n * 100:.1f}%)"
        )
        self.stdout.write(
            f"  폴백(as-of 경쟁강도 없음): {s['b_fallback_no_asof']}건 / "
            f"폴백(정책 게이트): {s['b_fallback_policy_gate']}건"
        )

        summary_a = self._model_summary(records, "a")
        summary_b = self._model_summary(records, "b")
        self._print_ab_table("전체", summary_a, summary_b)

        applied = [r for r in records if r["b_applied"]]
        if applied:
            self._print_ab_table(
                f"B 적용 서브셋 ({len(applied)}건)",
                self._model_summary(applied, "a"),
                self._model_summary(applied, "b"),
            )

        # 세그먼트별
        segments = self._segment_summary(records)
        self.stdout.write("")
        self.stdout.write("[세그먼트별 (price_seg × 실현 bidder 버킷)]")
        self.stdout.write(
            f"{'세그먼트':<16s} {'n':>4s} {'MAE_A':>8s} {'MAE_B':>8s} "
            f"{'ΔMAE':>8s} {'B적용':>5s} {'폴백':>5s}"
        )
        for seg_key, seg in segments.items():
            self.stdout.write(
                f"{seg_key:<16s} {seg['n']:>4d} {seg['mae_a_pp']:>8.3f} "
                f"{seg['mae_b_pp']:>8.3f} {seg['delta_mae_pp']:>+8.3f} "
                f"{seg['b_applied']:>5d} {seg['b_fallback']:>5d}"
            )

    def _print_ab_table(self, title: str, sa: dict, sb: dict):
        self.stdout.write("")
        self.stdout.write(f"[A/B 비교 — {title}]")
        rows = [
            ("MAE (%p)", "mae_pp", "{:.4f}"),
            ("중앙값 |오차| (%p)", "median_abs_err_pp", "{:.4f}"),
            ("평균 오차 (%p, +=과대)", "avg_err_pp", "{:+.4f}"),
            ("과대추천 비율", "over_recommend_rate", "{:.1%}"),
            ("실전 하한율 통과율", "realized_floor_pass_rate", "{:.1%}"),
            ("serving 하한 통과율", "serving_floor_pass_rate", "{:.1%}"),
            ("순공사원가98 통과율(추정)", "net_cost_pass_rate_estimated", "{:.1%}"),
        ]
        self.stdout.write(f"  {'지표':<26s} {'모델 A':>12s} {'모델 B':>12s}")
        for label, key, fmt in rows:
            va = fmt.format(sa[key]) if sa else "-"
            vb = fmt.format(sb[key]) if sb else "-"
            self.stdout.write(f"  {label:<26s} {va:>12s} {vb:>12s}")

    # ──────────────────────────────────────────
    # JSON 저장
    # ──────────────────────────────────────────

    def _save_json(self, results: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)

        records = results["records"]
        applied = [r for r in records if r["b_applied"]]
        report = {
            "meta": results["meta"],
            "stats": results["stats"],
            "overall": {
                "model_a": self._model_summary(records, "a"),
                "model_b": self._model_summary(records, "b"),
            },
            "b_applied_subset": {
                "n": len(applied),
                "model_a": self._model_summary(applied, "a"),
                "model_b": self._model_summary(applied, "b"),
            },
            "by_segment": self._segment_summary(records),
            "records": records,
        }
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"JSON 저장: {path}"))
