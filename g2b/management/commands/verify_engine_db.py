"""BC-31: DB 대규모 코어엔진 검증.

수집된 A값/복수예비가격 + BidResult 전체 입찰자 데이터로 3계층 검증 수행.
BC-30 (558건/나의방)에서 1,000건+(DB/전체 입찰자)로 검증 범위 확장.

핵심 차이 (BC-30 대비):
  - 공고당 전체 입찰자 점수 계산
  - openg_rank vs 가격점수 순위 직접 대조
  - 수만 건 점수 역산

사용:
    python manage.py verify_engine_db                         # 전체 검증
    python manage.py verify_engine_db --limit 5               # 테스트
    python manage.py verify_engine_db --bid-no R25BK01238858  # 특정 공고
    python manage.py verify_engine_db --output data/collected/db_verification.json
"""

import json
from collections import defaultdict
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from math import floor
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
    WorkType,
    calculate_a_value,
    calc_price_score,
    select_table,
    TABLE_PARAMS_MAP,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 검증용 TABLE_PARAMS (float) — Decimal 변환 없이 역산
VERIFY_TABLE_PARAMS = {
    "TABLE_1": {"max_score": 50, "coeff": 2, "fixed_ratio": 0.925, "fixed_score": 45},
    "TABLE_2A": {"max_score": 70, "coeff": 4, "fixed_ratio": 0.9125, "fixed_score": 65},
    "TABLE_2B": {"max_score": 70, "coeff": 20, "fixed_ratio": 0.9025, "fixed_score": 65},
    "TABLE_3": {"max_score": 80, "coeff": 20, "fixed_ratio": 0.9025, "fixed_score": 75},
    "TABLE_4": {"max_score": 90, "coeff": 20, "fixed_ratio": 0.9025, "fixed_score": 85},
    "TABLE_5": {"max_score": 90, "coeff": 20, "fixed_ratio": 0.9025, "fixed_score": 85},
}


class Command(BaseCommand):
    help = "BC-31: DB 대규모 코어엔진 검증 (3계층)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=0,
            help="검증 대상 공고 수 (0=전체)",
        )
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로",
        )
        parser.add_argument(
            "--bid-no", type=str, default="",
            help="특정 공고번호만 검증",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        output_path = options["output"]
        bid_no = options["bid_no"]

        # 1. 수집 완료된 공고 목록 조회
        self.stdout.write("수집 완료 공고 목록 조회 중...")
        targets = self._get_targets(limit, bid_no)
        self.stdout.write(f"  검증 대상: {len(targets)}건")

        if not targets:
            self.stdout.write(self.style.WARNING("검증 대상 없음"))
            return

        # 2. A값/복수예비가격 로드
        self.stdout.write("A값/복수예비가격 DB 로드 중...")
        a_values_map = self._load_a_values(targets)
        prelim_map = self._load_prelim_prices(targets)
        self.stdout.write(
            f"  A값: {len(a_values_map)}건, 복수예비가격: {len(prelim_map)}건"
        )

        # 3. 공고별 전체 입찰자 점수 계산
        self.stdout.write("공고별 전체 입찰자 점수 계산 중...")
        results = self._compute_all(targets, a_values_map, prelim_map)

        # 4. 3계층 검증
        verification = self._verify(results, a_values_map, prelim_map)

        # 5. 리포트 출력
        self._print_summary(results)
        self._print_verification(verification)

        # 6. JSON 저장
        if output_path:
            self._save_json(results, verification, output_path)

    # ──────────────────────────────────────────
    # 대상 추출
    # ──────────────────────────────────────────

    def _get_targets(
        self, limit: int, bid_no: str,
    ) -> list[tuple[str, str]]:
        """수집 완료된 공고 목록 조회."""
        qs = BidApiCollectionLog.objects.filter(
            Q(a_value_status__in=["ok", "empty"]),
            Q(prelim_status__in=["ok", "empty"]),
        )

        if bid_no:
            qs = qs.filter(bid_ntce_no=bid_no)

        qs = qs.values_list("bid_ntce_no", "bid_ntce_ord").order_by("-bid_ntce_no")

        if limit > 0:
            return list(qs[:limit])
        return list(qs)

    def _load_a_values(
        self, targets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], AValueItems]:
        """A값 DB → {(ntce_no, ntce_ord): AValueItems}."""
        result = {}
        for ntce_no, ntce_ord in targets:
            try:
                row = BidApiAValue.objects.get(
                    bid_ntce_no=ntce_no, bid_ntce_ord=ntce_ord,
                )
                result[(ntce_no, ntce_ord)] = AValueItems(
                    national_pension=row.national_pension,
                    health_insurance=row.health_insurance,
                    retirement_mutual_aid=row.retirement_mutual_aid,
                    long_term_care=row.long_term_care,
                    occupational_safety=row.occupational_safety,
                    safety_management=row.safety_management,
                    quality_management=row.quality_management,
                )
            except BidApiAValue.DoesNotExist:
                pass
        return result

    def _load_prelim_prices(
        self, targets: list[tuple[str, str]],
    ) -> dict[tuple[str, str], list[dict]]:
        """복수예비가격 DB → {(ntce_no, ntce_ord): [price_dicts]}."""
        result = {}
        for ntce_no, ntce_ord in targets:
            rows = (
                BidApiPrelimPrice.objects
                .filter(bid_ntce_no=ntce_no, bid_ntce_ord=ntce_ord)
                .order_by("sequence_no")
            )
            if rows.exists():
                result[(ntce_no, ntce_ord)] = [
                    {
                        "basis_planned_price": r.basis_planned_price,
                        "is_drawn": r.is_drawn,
                        "draw_count": r.draw_count,
                        "planned_price": r.planned_price,
                        "base_amount": r.base_amount,
                    }
                    for r in rows
                ]
        return result

    # ──────────────────────────────────────────
    # 전체 입찰자 점수 계산
    # ──────────────────────────────────────────

    def _compute_all(
        self,
        targets: list[tuple[str, str]],
        a_values_map: dict[tuple[str, str], AValueItems],
        prelim_map: dict[tuple[str, str], list[dict]],
    ) -> dict:
        """공고별 전체 입찰자 점수를 계산한다."""
        announcements = []
        stats = {
            "total_announcements": len(targets),
            "success": 0,
            "skip_no_estimated": 0,
            "skip_no_presume": 0,
            "skip_out_of_scope": 0,
            "skip_a_exceeds_est": 0,
            "error": 0,
            "total_bidders_scored": 0,
            "total_bidders_skipped": 0,
        }
        table_dist = defaultdict(int)

        for idx, (ntce_no, ntce_ord) in enumerate(targets, 1):
            if idx % 100 == 0:
                self.stdout.write(f"  진행: {idx}/{len(targets)}")

            ann = {"bid_ntce_no": ntce_no, "bid_ntce_ord": ntce_ord}

            # BidResult에서 해당 공고의 전체 입찰자 조회
            bidders = list(
                BidResult.objects.filter(
                    bid_ntce_no=ntce_no,
                    bid_ntce_ord=ntce_ord,
                ).values(
                    "company_bizno", "company_nm", "openg_rank",
                    "bid_amt", "bid_rate", "estimated_price",
                    "presume_price", "base_amt",
                )
            )

            if not bidders:
                ann["status"] = "no_bidders"
                stats["error"] += 1
                announcements.append(ann)
                continue

            # 추정가격/예정가격: 첫 번째 입찰자에서 가져오기 (공고 공통)
            first = bidders[0]
            presume_price = first["presume_price"]
            estimated_price = first["estimated_price"]
            base_amt = first["base_amt"]

            ann["presume_price"] = presume_price
            ann["estimated_price"] = estimated_price
            ann["base_amt"] = base_amt
            ann["bidder_count"] = len(bidders)

            if not presume_price or presume_price <= 0:
                ann["status"] = "skip_no_presume"
                stats["skip_no_presume"] += 1
                announcements.append(ann)
                continue

            if not estimated_price or estimated_price <= 0:
                ann["status"] = "skip_no_estimated"
                stats["skip_no_estimated"] += 1
                announcements.append(ann)
                continue

            # 별표 라우팅 (추정가격 기준)
            try:
                table_type = select_table(presume_price, WorkType.CONSTRUCTION)
            except ValueError as e:
                ann["status"] = "error"
                ann["error"] = str(e)
                stats["error"] += 1
                announcements.append(ann)
                continue

            ann["table_type"] = table_type.value
            table_dist[table_type.value] += 1

            if table_type == TableType.OUT_OF_SCOPE:
                ann["status"] = "out_of_scope"
                stats["skip_out_of_scope"] += 1
                announcements.append(ann)
                continue

            # A값
            a_items = a_values_map.get((ntce_no, ntce_ord), AValueItems())
            a_value = calculate_a_value(a_items)
            ann["a_value"] = a_value
            ann["a_source"] = (
                "api" if (ntce_no, ntce_ord) in a_values_map else "zero"
            )

            if a_value >= estimated_price:
                ann["status"] = "a_exceeds_est"
                stats["skip_a_exceeds_est"] += 1
                announcements.append(ann)
                continue

            # 각 입찰자 점수 계산
            scored_bidders = []
            for bidder in bidders:
                bid_amt = bidder["bid_amt"]
                if not bid_amt or bid_amt <= 0:
                    stats["total_bidders_skipped"] += 1
                    continue

                try:
                    result = calc_price_score(
                        bid_amt, estimated_price, a_value, table_type,
                    )
                    scored_bidders.append({
                        "company_bizno": bidder["company_bizno"],
                        "company_nm": bidder["company_nm"],
                        "openg_rank": bidder["openg_rank"],
                        "bid_amt": bid_amt,
                        "score": float(result.score),
                        "ratio": float(result.ratio),
                        "is_fixed": result.is_fixed_score,
                    })
                    stats["total_bidders_scored"] += 1
                except Exception:
                    stats["total_bidders_skipped"] += 1

            ann["scored_bidders"] = scored_bidders
            ann["status"] = "success"
            stats["success"] += 1
            announcements.append(ann)

        self.stdout.write(f"  완료: {stats['success']}건 성공")

        return {
            "stats": stats,
            "announcements": announcements,
            "table_dist": dict(table_dist),
        }

    # ──────────────────────────────────────────
    # 3계층 검증
    # ──────────────────────────────────────────

    def _verify(
        self,
        results: dict,
        a_values_map: dict[tuple[str, str], AValueItems],
        prelim_map: dict[tuple[str, str], list[dict]],
    ) -> dict:
        """3계층 교차 검증."""
        v = {
            "layer1_input": {},
            "layer2_formula": {},
            "layer3_reality": {},
            "verdict": "PASS",
        }

        announcements = results["announcements"]
        success_anns = [a for a in announcements if a.get("status") == "success"]

        # ── 계층 1: 입력 검증 ──

        # 1a. 예정가격: 추첨평균 vs BidResult.estimated_price
        det_tested = det_passed = 0
        for ann in success_anns:
            key = (ann["bid_ntce_no"], ann["bid_ntce_ord"])
            prelim = prelim_map.get(key)
            if not prelim:
                continue

            drawn = [p for p in prelim if p["is_drawn"]]
            if not drawn:
                continue

            # 추첨 예비가격 평균
            drawn_avg = sum(p["basis_planned_price"] for p in drawn) / len(drawn)
            recalc = (
                floor(drawn_avg) if drawn_avg != int(drawn_avg) else int(drawn_avg)
            )

            # API plnprc (첫 레코드)
            api_plnprc = prelim[0]["planned_price"]

            # BidResult.estimated_price
            db_est = ann["estimated_price"]

            det_tested += 1
            # 3자 대조: 추첨평균 == API == DB
            if recalc == api_plnprc and api_plnprc == db_est:
                det_passed += 1

        v["layer1_input"]["det_price_3way"] = {
            "tested": det_tested, "passed": det_passed,
        }

        # 1b. 기초금액: API base_amount vs BidResult.base_amt
        base_tested = base_passed = 0
        for ann in success_anns:
            key = (ann["bid_ntce_no"], ann["bid_ntce_ord"])
            prelim = prelim_map.get(key)
            if not prelim:
                continue

            api_base = prelim[0]["base_amount"]
            db_base = ann.get("base_amt")
            if api_base and db_base:
                base_tested += 1
                if api_base == db_base:
                    base_passed += 1

        v["layer1_input"]["base_amt_2way"] = {
            "tested": base_tested, "passed": base_passed,
        }

        # 1c. A값 합산: raw 7항목 합 vs calculate_a_value() 결과
        asum_tested = asum_passed = 0
        for ann in success_anns:
            key = (ann["bid_ntce_no"], ann["bid_ntce_ord"])
            a_items = a_values_map.get(key)
            if a_items is None:
                continue

            raw_sum = sum([
                a_items.national_pension,
                a_items.health_insurance,
                a_items.retirement_mutual_aid,
                a_items.long_term_care,
                a_items.occupational_safety,
                a_items.safety_management,
                a_items.quality_management,
            ])
            asum_tested += 1
            if raw_sum == ann.get("a_value", -1):
                asum_passed += 1

        v["layer1_input"]["a_value_sum"] = {
            "tested": asum_tested, "passed": asum_passed,
        }

        # ── 계층 2: 수식 검증 ──

        ratio_tested = ratio_passed = 0
        score_tested = score_passed = 0
        fixed_tested = fixed_passed = 0

        for ann in success_anns:
            table_str = ann.get("table_type")
            if table_str not in VERIFY_TABLE_PARAMS:
                continue
            params = VERIFY_TABLE_PARAMS[table_str]
            est = ann["estimated_price"]
            a_val = ann.get("a_value", 0)

            for bidder in ann.get("scored_bidders", []):
                bid = bidder["bid_amt"]
                stored_ratio = bidder["ratio"]
                stored_score = bidder["score"]
                stored_fixed = bidder["is_fixed"]

                # ratio 역산
                d_ratio = Decimal(str(bid - a_val)) / Decimal(str(est - a_val))
                q = Decimal(10) ** -4
                recalc_ratio = float(d_ratio.quantize(q, rounding=ROUND_HALF_UP))
                ratio_tested += 1
                if abs(recalc_ratio - stored_ratio) < 0.00005:
                    ratio_passed += 1

                # 고정점수 조건
                is_fixed = (
                    bid <= est and recalc_ratio >= params["fixed_ratio"]
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

        # 3a. 가격점수 순위 vs openg_rank 비교
        rank_tested = 0
        rank_top1_match = 0
        rank_top3_match = 0

        for ann in success_anns:
            scored = ann.get("scored_bidders", [])
            if len(scored) < 2:
                continue

            # 가격점수 내림차순 정렬
            by_score = sorted(scored, key=lambda b: b["score"], reverse=True)

            # 실제 1위 (openg_rank == "1")
            actual_rank1 = {
                b["company_bizno"] for b in scored
                if str(b.get("openg_rank", "")).strip() == "1"
            }
            if not actual_rank1:
                continue

            rank_tested += 1

            # 가격점수 1위가 실제 1위인지
            score_rank1_bizno = by_score[0]["company_bizno"]
            if score_rank1_bizno in actual_rank1:
                rank_top1_match += 1

            # 가격점수 상위 3명에 실제 1위가 포함되어 있는지
            score_top3 = {b["company_bizno"] for b in by_score[:3]}
            if actual_rank1 & score_top3:
                rank_top3_match += 1

        v["layer3_reality"]["rank_comparison"] = {
            "tested": rank_tested,
            "score_top1_is_actual_top1": rank_top1_match,
            "score_top1_rate": (
                round(rank_top1_match / rank_tested, 3) if rank_tested else 0
            ),
            "actual_top1_in_score_top3": rank_top3_match,
            "top3_rate": (
                round(rank_top3_match / rank_tested, 3) if rank_tested else 0
            ),
        }

        # 3b. 점수 분포 통계
        all_scores = []
        for ann in success_anns:
            for b in ann.get("scored_bidders", []):
                all_scores.append(b["score"])

        if all_scores:
            all_scores.sort()
            n = len(all_scores)
            avg = sum(all_scores) / n
            median = all_scores[n // 2]
            variance = sum((s - avg) ** 2 for s in all_scores) / n
            std = variance ** 0.5
            v["layer3_reality"]["score_distribution"] = {
                "count": n,
                "mean": round(avg, 2),
                "median": round(median, 2),
                "std": round(std, 2),
                "min": round(all_scores[0], 2),
                "max": round(all_scores[-1], 2),
            }

        # ── 종합 판정 ──
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

    # ──────────────────────────────────────────
    # 리포트 출력
    # ──────────────────────────────────────────

    def _print_summary(self, results: dict):
        s = results["stats"]
        self.stdout.write("")
        self.stdout.write("=" * 55)
        self.stdout.write("  DB 대규모 코어엔진 검증 (BC-31)")
        self.stdout.write("=" * 55)
        self.stdout.write(f"검증 대상 공고:       {s['total_announcements']}건")
        self.stdout.write(f"성공:                 {s['success']}건")
        self.stdout.write(f"스킵 (추정가격 없음): {s['skip_no_presume']}건")
        self.stdout.write(f"스킵 (예정가격 없음): {s['skip_no_estimated']}건")
        self.stdout.write(f"스킵 (>=100억):       {s['skip_out_of_scope']}건")
        self.stdout.write(f"스킵 (A>=예정가격):   {s['skip_a_exceeds_est']}건")
        self.stdout.write(f"에러:                 {s['error']}건")
        self.stdout.write("")
        self.stdout.write(f"총 입찰자 점수 계산:  {s['total_bidders_scored']}건")
        self.stdout.write(f"입찰자 스킵:          {s['total_bidders_skipped']}건")

        # 별표 분포
        self.stdout.write("")
        self.stdout.write("[별표 분포]")
        dist = results["table_dist"]
        for table in [
            "TABLE_5", "TABLE_4", "TABLE_3",
            "TABLE_2A", "TABLE_2B", "TABLE_1", "OUT_OF_SCOPE",
        ]:
            if dist.get(table, 0) > 0:
                self.stdout.write(f"  {table:<14s}: {dist[table]:>5d}건")

    def _print_verification(self, v: dict):
        self.stdout.write("")
        self.stdout.write("=" * 55)
        self.stdout.write("  교차 검증 (3계층)")
        self.stdout.write("=" * 55)

        # 계층 1
        self.stdout.write("")
        self.stdout.write("[계층 1: 입력 검증]")
        for label, key in [
            ("예정가격 (추첨평균 vs API vs DB)", "det_price_3way"),
            ("기초금액 (API vs DB, 참고)", "base_amt_2way"),
            ("A값 합산 (raw 7항목 vs 엔진)", "a_value_sum"),
        ]:
            d = v["layer1_input"].get(key, {})
            t, p = d.get("tested", 0), d.get("passed", 0)
            pct = f"{p / t * 100:.1f}" if t > 0 else "-"
            mark = "\u2705" if t > 0 and p == t else ("\u274c" if t > 0 else "\u2796")
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
            mark = "\u2705" if t > 0 and p == t else ("\u274c" if t > 0 else "\u2796")
            self.stdout.write(f"  {mark} {label}: {p}/{t} ({pct}%)")

        # 계층 3
        self.stdout.write("")
        self.stdout.write("[계층 3: 현실 정합성]")
        rank_cmp = v["layer3_reality"].get("rank_comparison", {})
        if rank_cmp.get("tested", 0) > 0:
            self.stdout.write(
                f"  가격점수 1위 = 실제 1위: "
                f"{rank_cmp['score_top1_is_actual_top1']}/{rank_cmp['tested']}건 "
                f"({rank_cmp['score_top1_rate'] * 100:.1f}%)"
            )
            self.stdout.write(
                f"  실제 1위가 점수 상위3에 포함: "
                f"{rank_cmp['actual_top1_in_score_top3']}/{rank_cmp['tested']}건 "
                f"({rank_cmp['top3_rate'] * 100:.1f}%)"
            )

        score_dist = v["layer3_reality"].get("score_distribution", {})
        if score_dist:
            self.stdout.write(
                f"  점수 분포: 평균 {score_dist['mean']}점, "
                f"중앙값 {score_dist['median']}점, "
                f"표준편차 {score_dist['std']}점"
            )
            self.stdout.write(
                f"  범위: {score_dist['min']} ~ {score_dist['max']}점 "
                f"(총 {score_dist['count']:,}건)"
            )

        # 종합 판정
        verdict = v["verdict"]
        self.stdout.write("")
        self.stdout.write("=" * 55)
        if verdict == "PASS":
            self.stdout.write(
                self.style.SUCCESS("  종합 판정: \u2705 코어엔진 검증 통과")
            )
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

    def _save_json(self, results: dict, verification: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path

        path.parent.mkdir(parents=True, exist_ok=True)

        # scored_bidders를 요약으로 대체 (수만 건 전체 저장은 과도)
        ann_summary = []
        for ann in results["announcements"]:
            summary = {k: v for k, v in ann.items() if k != "scored_bidders"}
            scored = ann.get("scored_bidders", [])
            if scored:
                scores = [b["score"] for b in scored]
                summary["bidders_scored"] = len(scored)
                summary["score_mean"] = round(sum(scores) / len(scores), 2)
                summary["score_max"] = max(scores)
                summary["score_min"] = min(scores)
            ann_summary.append(summary)

        report = {
            "meta": {
                "command": "verify_engine_db",
                "bc_id": "BC-31",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "schema_version": "1.0",
            },
            "stats": results["stats"],
            "table_distribution": results["table_dist"],
            "verification": verification,
            "announcements": ann_summary,
        }

        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"JSON 저장: {path}"))
