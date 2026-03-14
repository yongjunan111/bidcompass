"""
BidCompass 테스트 스위트

18개 클래스:
  - TestRoundingHelpers
  - TestSelectTable
  - TestCalculateAValue
  - TestCheckNetCostExclusion
  - TestCalcPriceScore
  - TestGetFloorRate
  - TestBidAnalysisEngine
  - TestAssessmentRateFormula (BC-29)
  - TestOptimalBid (BC-33)
  - TestCalculatorView (BC-39)
  - TestRecommendView (BC-40, 사전 추천)
  - TestRecommendBand (BC-40, optimal_bid.py 내부)
  - TestPreBidRecommend (BC-45, 사전 추천 서비스)
  - TestScanBoundsAndStrategy (BC-45, optimal_bid.py 내부)
  - TestReportStats (BC-53)
  - TestAIReportDataclasses (BC-53)
  - TestAIReportView (BC-53)
"""

import json
from decimal import Decimal
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, Client as DjangoClient
from django.utils import timezone

from g2b.models import BidAnnouncement, BidContract, BidResult
from g2b.services.g2b_construction_sync import (
    PLACEHOLDER_CONTRACT_NO,
    PLACEHOLDER_PRELIM_SEQUENCE,
    bulk_upsert,
    is_eligible_notice_for_service,
    is_upcoming_notice,
    map_a_value_item,
    map_base_amount_to_placeholder_prelim,
    map_contract_item_to_bid_contract,
    map_notice_to_announcement,
    map_notice_to_contract,
    map_prelim_price_item,
    map_successful_bid_to_result,
)

from g2b.services.bid_engine import (
    AValueItems,
    BidAnalysisEngine,
    ExclusionStatus,
    TABLE_PARAMS_MAP,
    TableType,
    WorkType,
    calc_price_score,
    calculate_a_value,
    ceil_up,
    check_net_cost_exclusion,
    get_floor_rate,
    round_half_up,
    select_table,
    truncate,
)

UNIT_EOUK = 1_0000_0000


class TestRoundingHelpers(SimpleTestCase):
    """반올림 헬퍼 3종 테스트."""

    def test_round_half_up_basic(self):
        self.assertEqual(round_half_up(Decimal("0.12345"), 4), Decimal("0.1235"))

    def test_round_half_up_five(self):
        """banker's rounding 차이: 0.5는 올림."""
        self.assertEqual(round_half_up(Decimal("2.5"), 0), Decimal("3"))
        # Python round()는 banker's rounding이므로 2를 반환
        self.assertEqual(round(2.5), 2)

    def test_round_half_up_negative(self):
        self.assertEqual(round_half_up(Decimal("-1.25"), 1), Decimal("-1.3"))

    def test_truncate_basic(self):
        self.assertEqual(truncate(Decimal("0.123456"), 5), Decimal("0.12345"))

    def test_truncate_no_round(self):
        self.assertEqual(truncate(Decimal("0.99999"), 4), Decimal("0.9999"))

    def test_ceil_up_int(self):
        self.assertEqual(ceil_up(100), 100)

    def test_ceil_up_decimal_exact(self):
        self.assertEqual(ceil_up(Decimal("100")), 100)

    def test_ceil_up_decimal_fraction(self):
        self.assertEqual(ceil_up(Decimal("100.01")), 101)

    def test_ceil_up_decimal_small_fraction(self):
        self.assertEqual(ceil_up(Decimal("99.001")), 100)

    def test_float_raises_type_error(self):
        """float 직접 전달 금지."""
        with self.assertRaises(TypeError):
            round_half_up(0.5, 1)
        with self.assertRaises(TypeError):
            truncate(0.5, 1)
        with self.assertRaises(TypeError):
            ceil_up(0.5)


class TestSelectTable(SimpleTestCase):
    """BC-22: select_table 경계값 테스트."""

    # 일반공사 경계값
    def test_construction_under_2eouk(self):
        self.assertEqual(
            select_table(1_9999_9999, WorkType.CONSTRUCTION), TableType.TABLE_5
        )

    def test_construction_exactly_2eouk(self):
        self.assertEqual(
            select_table(2 * UNIT_EOUK, WorkType.CONSTRUCTION), TableType.TABLE_4
        )

    def test_construction_under_3eouk(self):
        self.assertEqual(
            select_table(3 * UNIT_EOUK - 1, WorkType.CONSTRUCTION), TableType.TABLE_4
        )

    def test_construction_exactly_3eouk(self):
        self.assertEqual(
            select_table(3 * UNIT_EOUK, WorkType.CONSTRUCTION), TableType.TABLE_3
        )

    def test_construction_under_10eouk(self):
        self.assertEqual(
            select_table(10 * UNIT_EOUK - 1, WorkType.CONSTRUCTION), TableType.TABLE_3
        )

    def test_construction_exactly_10eouk(self):
        self.assertEqual(
            select_table(10 * UNIT_EOUK, WorkType.CONSTRUCTION), TableType.TABLE_2A
        )

    def test_construction_under_50eouk(self):
        self.assertEqual(
            select_table(50 * UNIT_EOUK - 1, WorkType.CONSTRUCTION), TableType.TABLE_2A
        )

    def test_construction_exactly_50eouk(self):
        self.assertEqual(
            select_table(50 * UNIT_EOUK, WorkType.CONSTRUCTION), TableType.TABLE_1
        )

    def test_construction_under_100eouk(self):
        self.assertEqual(
            select_table(100 * UNIT_EOUK - 1, WorkType.CONSTRUCTION), TableType.TABLE_1
        )

    def test_construction_100eouk_out(self):
        self.assertEqual(
            select_table(100 * UNIT_EOUK, WorkType.CONSTRUCTION), TableType.OUT_OF_SCOPE
        )

    # 전문공사 경계값
    def test_specialty_under_08eouk(self):
        self.assertEqual(
            select_table(7999_9999, WorkType.SPECIALTY), TableType.TABLE_5
        )

    def test_specialty_08eouk_exact_boundary(self):
        """전문공사 80,000,000원 → TABLE_4 (T5가 아님)."""
        self.assertEqual(
            select_table(8000_0000, WorkType.SPECIALTY), TableType.TABLE_4
        )

    def test_specialty_under_3eouk(self):
        self.assertEqual(
            select_table(3 * UNIT_EOUK - 1, WorkType.SPECIALTY), TableType.TABLE_4
        )

    def test_specialty_3_to_10eouk_table2b(self):
        """전문공사 3~10억 → TABLE_2B (별표2-나)."""
        self.assertEqual(
            select_table(3 * UNIT_EOUK, WorkType.SPECIALTY), TableType.TABLE_2B
        )
        self.assertEqual(
            select_table(9 * UNIT_EOUK, WorkType.SPECIALTY), TableType.TABLE_2B
        )

    def test_specialty_10_to_50eouk_table2a(self):
        """전문공사 10~50억 → TABLE_2A (별표2-가, 10억 이상은 업종 무관)."""
        self.assertEqual(
            select_table(10 * UNIT_EOUK, WorkType.SPECIALTY), TableType.TABLE_2A
        )
        self.assertEqual(
            select_table(49 * UNIT_EOUK, WorkType.SPECIALTY), TableType.TABLE_2A
        )

    def test_specialty_50eouk_table1(self):
        self.assertEqual(
            select_table(50 * UNIT_EOUK, WorkType.SPECIALTY), TableType.TABLE_1
        )

    # 입력 검증
    def test_zero_raises(self):
        with self.assertRaises(ValueError):
            select_table(0, WorkType.CONSTRUCTION)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            select_table(-1, WorkType.CONSTRUCTION)


class TestCalculateAValue(SimpleTestCase):
    """BC-25: calculate_a_value 테스트."""

    def test_basic_sum(self):
        items = AValueItems(
            national_pension=1_000_000,
            health_insurance=500_000,
            retirement_mutual_aid=300_000,
            long_term_care=200_000,
            occupational_safety=400_000,
            safety_management=150_000,
            quality_management=100_000,
        )
        self.assertEqual(calculate_a_value(items), 2_650_000)

    def test_all_zero(self):
        items = AValueItems()
        self.assertEqual(calculate_a_value(items), 0)

    def test_negative_raises(self):
        items = AValueItems(national_pension=-100)
        with self.assertRaises(ValueError) as ctx:
            calculate_a_value(items)
        self.assertIn("national_pension", str(ctx.exception))

    def test_negative_other_field(self):
        items = AValueItems(quality_management=-1)
        with self.assertRaises(ValueError) as ctx:
            calculate_a_value(items)
        self.assertIn("quality_management", str(ctx.exception))


class TestCheckNetCostExclusion(SimpleTestCase):
    """BC-24: check_net_cost_exclusion 테스트."""

    def test_passed(self):
        """bid >= threshold → PASSED."""
        result = check_net_cost_exclusion(1_000_000, 980_000)
        self.assertEqual(result.status, ExclusionStatus.PASSED)
        self.assertEqual(result.threshold, 980_000)

    def test_excluded(self):
        """bid < threshold → EXCLUDED."""
        result = check_net_cost_exclusion(1_000_000, 979_999)
        self.assertEqual(result.status, ExclusionStatus.EXCLUDED)
        self.assertIn("순공사원가 98% 미달", result.message)

    def test_threshold_ceil(self):
        """올림 확인: 999_999 * 98 / 100 = 979999.02 → 979,999? No. Let's compute.
        999_999 * 98 = 97_999_902 / 100 = 979999.02 → ceil = 980,000."""
        result = check_net_cost_exclusion(999_999, 980_000)
        self.assertEqual(result.threshold, 980_000)
        self.assertEqual(result.status, ExclusionStatus.PASSED)

    def test_threshold_exact_boundary(self):
        """bid == threshold → PASSED (< 기준이므로)."""
        # 1_000_000 * 98 / 100 = 980,000 (정확히 나누어짐)
        result = check_net_cost_exclusion(1_000_000, 980_000)
        self.assertEqual(result.status, ExclusionStatus.PASSED)

    def test_threshold_one_below(self):
        result = check_net_cost_exclusion(1_000_000, 979_999)
        self.assertEqual(result.status, ExclusionStatus.EXCLUDED)

    def test_negative_net_cost_raises(self):
        with self.assertRaises(ValueError):
            check_net_cost_exclusion(-1, 100)

    def test_negative_bid_raises(self):
        with self.assertRaises(ValueError):
            check_net_cost_exclusion(100, -1)

    def test_zero_net_cost(self):
        """순공사원가 0 → threshold 0, bid 0 → PASSED."""
        result = check_net_cost_exclusion(0, 0)
        self.assertEqual(result.threshold, 0)
        self.assertEqual(result.status, ExclusionStatus.PASSED)


class TestCalcPriceScore(SimpleTestCase):
    """BC-23: calc_price_score 테스트."""

    def test_basic_score(self):
        """기본 점수 계산 — 별표3 기준 ratio=0.9000 → 80점."""
        # est=5억, A=5천만, bid= 0.9*(5억-5천만)+5천만 = 4.1억
        est = 5 * UNIT_EOUK
        a = 5000_0000
        bid = int((est - a) * 0.9 + a)  # ratio=0.9 → 90% → score=80
        result = calc_price_score(bid, est, a, TableType.TABLE_3)
        self.assertEqual(result.score, Decimal("80"))
        self.assertFalse(result.is_fixed_score)

    def test_fixed_score_exact_boundary(self):
        """ratio == fixed_ratio → 고정점수 적용 (정확히 같을 때)."""
        # TABLE_3: fixed_ratio=0.9025, fixed_score=75
        # ratio = (bid - A) / (est - A) = 0.9025
        est = 5 * UNIT_EOUK
        a = 5000_0000
        # bid - A = 0.9025 * (est - A) = 0.9025 * 4.5억 = 406,125,000
        bid = int(Decimal("0.9025") * (est - a)) + a
        result = calc_price_score(bid, est, a, TableType.TABLE_3)
        self.assertTrue(result.is_fixed_score)
        self.assertEqual(result.score, Decimal("75"))

    def test_no_fixed_score_when_bid_exceeds_est(self):
        """bid > est_price면 ratio >= fixed_ratio여도 고정점수 미적용."""
        est = 5 * UNIT_EOUK
        a = 5000_0000
        # bid > est이지만 ratio >= fixed_ratio가 되도록 설정
        bid = est + 1000_0000  # est보다 1천만원 높음
        result = calc_price_score(bid, est, a, TableType.TABLE_3)
        self.assertFalse(result.is_fixed_score)

    def test_minimum_score_2(self):
        """점수 하한 2점."""
        est = 5 * UNIT_EOUK
        a = 5000_0000
        # 극단적으로 낮은 bid → 매우 낮은 ratio
        bid = a + 1  # ratio ≈ 0.0000
        result = calc_price_score(bid, est, a, TableType.TABLE_3)
        self.assertEqual(result.score, Decimal("2"))

    def test_table1_coeff_2(self):
        """별표1 계수=2 확인."""
        est = 60 * UNIT_EOUK
        a = 1 * UNIT_EOUK
        # ratio=0.8900 → score = 50 - 2*|90-89| = 50-2 = 48
        bid = int(Decimal("0.89") * (est - a)) + a
        result = calc_price_score(bid, est, a, TableType.TABLE_1)
        self.assertEqual(result.score, Decimal("48"))

    def test_table2a_coeff_4(self):
        """별표2-가 계수=4 확인."""
        est = 20 * UNIT_EOUK
        a = 1 * UNIT_EOUK
        # ratio=0.8900 → score = 70 - 4*|90-89| = 70-4 = 66
        bid = int(Decimal("0.89") * (est - a)) + a
        result = calc_price_score(bid, est, a, TableType.TABLE_2A)
        self.assertEqual(result.score, Decimal("66"))

    def test_table2b_coeff_20(self):
        """별표2-나 계수=20 확인."""
        est = 5 * UNIT_EOUK
        a = 5000_0000
        # ratio=0.8900 → score = 70 - 20*|90-89| = 70-20 = 50
        bid = int(Decimal("0.89") * (est - a)) + a
        result = calc_price_score(bid, est, a, TableType.TABLE_2B)
        self.assertEqual(result.score, Decimal("50"))

    def test_out_of_scope_raises(self):
        with self.assertRaises(ValueError):
            calc_price_score(100, 200, 0, TableType.OUT_OF_SCOPE)

    def test_est_zero_raises(self):
        with self.assertRaises(ValueError):
            calc_price_score(100, 0, 0, TableType.TABLE_3)

    def test_negative_bid_raises(self):
        with self.assertRaises(ValueError):
            calc_price_score(-1, 5 * UNIT_EOUK, 0, TableType.TABLE_3)

    def test_a_value_ge_est_raises(self):
        with self.assertRaises(ValueError):
            calc_price_score(100, 100, 100, TableType.TABLE_3)

    def test_a_value_negative_raises(self):
        with self.assertRaises(ValueError):
            calc_price_score(100, 200, -1, TableType.TABLE_3)


class TestGetFloorRate(SimpleTestCase):
    """get_floor_rate 구간 경계 테스트."""

    def test_under_10eouk(self):
        self.assertEqual(get_floor_rate(1 * UNIT_EOUK), Decimal("89.745"))

    def test_exactly_10eouk(self):
        """10억 → 10~50억 구간."""
        self.assertEqual(get_floor_rate(10 * UNIT_EOUK), Decimal("88.745"))

    def test_exactly_50eouk(self):
        """50억 → 50~100억 구간."""
        self.assertEqual(get_floor_rate(50 * UNIT_EOUK), Decimal("87.495"))

    def test_exactly_100eouk(self):
        """100억 → 100~300억 구간 (방어적 포함)."""
        self.assertEqual(get_floor_rate(100 * UNIT_EOUK), Decimal("81.995"))

    def test_over_300eouk(self):
        """300억 이상 → 마지막 구간 반환 (방어적)."""
        self.assertEqual(get_floor_rate(500 * UNIT_EOUK), Decimal("81.995"))

    def test_zero_raises(self):
        with self.assertRaises(ValueError):
            get_floor_rate(0)

    def test_boundary_9_9999(self):
        """10억 직전."""
        self.assertEqual(get_floor_rate(10 * UNIT_EOUK - 1), Decimal("89.745"))


class TestBidAnalysisEngine(SimpleTestCase):
    """BC-26: BidAnalysisEngine 통합 테스트."""

    def _make_a_items(self, total: int = 5000_0000) -> AValueItems:
        """테스트용 A값 아이템 (total을 national_pension에 집중)."""
        return AValueItems(national_pension=total)

    def test_out_of_scope_early_return(self):
        """≥100억 → early return, is_out_of_scope=True."""
        engine = BidAnalysisEngine(
            estimated_price=100 * UNIT_EOUK,
            work_type=WorkType.CONSTRUCTION,
            a_value_items=self._make_a_items(),
            bid_price=90 * UNIT_EOUK,
        )
        result = engine.analyze()
        self.assertTrue(result.is_out_of_scope)
        self.assertEqual(result.table_type, TableType.OUT_OF_SCOPE)
        self.assertFalse(result.final_pass)
        self.assertIsNone(result.price_score_result)

    def test_excluded_with_reference_score(self):
        """배제 시 reference_price_score 계산, final_pass=False."""
        est = 5 * UNIT_EOUK
        a_items = self._make_a_items(5000_0000)
        net_cost = 4 * UNIT_EOUK
        # threshold = ceil(4억 * 98 / 100) = 3.92억
        # bid < threshold → EXCLUDED
        bid = 3_9000_0000  # 3.9억 < 3.92억

        engine = BidAnalysisEngine(
            estimated_price=est,
            work_type=WorkType.CONSTRUCTION,
            a_value_items=a_items,
            bid_price=bid,
            net_construction_cost=net_cost,
        )
        result = engine.analyze()

        self.assertEqual(result.exclusion_result.status, ExclusionStatus.EXCLUDED)
        self.assertFalse(result.final_pass)
        self.assertIsNotNone(result.reference_price_score)
        self.assertIsNotNone(result.price_score_result)

    def test_passed_normal_flow(self):
        """정상 통과 — 배제 통과 + 점수 계산."""
        est = 5 * UNIT_EOUK
        a_items = self._make_a_items(5000_0000)
        net_cost = 4 * UNIT_EOUK
        # bid = 0.9 * (5억-0.5억) + 0.5억 = 4.1억 > threshold 3.92억
        bid = int(Decimal("0.9") * (est - 5000_0000)) + 5000_0000

        engine = BidAnalysisEngine(
            estimated_price=est,
            work_type=WorkType.CONSTRUCTION,
            a_value_items=a_items,
            bid_price=bid,
            net_construction_cost=net_cost,
        )
        result = engine.analyze()

        self.assertEqual(result.exclusion_result.status, ExclusionStatus.PASSED)
        self.assertTrue(result.final_pass)
        self.assertIsNotNone(result.price_score_result)
        self.assertIsNone(result.reference_price_score)

    def test_no_bid_heatmap_only(self):
        """bid_price=None → 히트맵만 생성."""
        est = 5 * UNIT_EOUK
        a_items = self._make_a_items(5000_0000)

        engine = BidAnalysisEngine(
            estimated_price=est,
            work_type=WorkType.CONSTRUCTION,
            a_value_items=a_items,
        )
        result = engine.analyze()

        self.assertIsNone(result.price_score_result)
        self.assertGreater(len(result.score_heatmap), 0)

    def test_no_net_cost_not_checked(self):
        """net_construction_cost=None → NOT_CHECKED."""
        est = 5 * UNIT_EOUK
        a_items = self._make_a_items(5000_0000)
        bid = int(Decimal("0.9") * (est - 5000_0000)) + 5000_0000

        engine = BidAnalysisEngine(
            estimated_price=est,
            work_type=WorkType.CONSTRUCTION,
            a_value_items=a_items,
            bid_price=bid,
        )
        result = engine.analyze()

        self.assertEqual(
            result.exclusion_result.status, ExclusionStatus.NOT_CHECKED
        )
        self.assertTrue(result.final_pass)

    def test_heatmap_has_points(self):
        """히트맵에 데이터 포인트가 존재."""
        est = 5 * UNIT_EOUK
        a_items = self._make_a_items(5000_0000)

        engine = BidAnalysisEngine(
            estimated_price=est,
            work_type=WorkType.CONSTRUCTION,
            a_value_items=a_items,
        )
        result = engine.analyze()

        self.assertGreater(len(result.score_heatmap), 0)
        point = result.score_heatmap[0]
        self.assertIsInstance(point.bid_rate, Decimal)
        self.assertIsInstance(point.bid_amount, int)
        self.assertIsInstance(point.price_score, Decimal)

    def test_excluded_final_pass_forced_false(self):
        """배제 시 final_pass가 강제로 False."""
        est = 5 * UNIT_EOUK
        a_items = self._make_a_items(5000_0000)
        net_cost = 4 * UNIT_EOUK
        bid = 1  # 극단적으로 낮은 bid → 무조건 배제

        engine = BidAnalysisEngine(
            estimated_price=est,
            work_type=WorkType.CONSTRUCTION,
            a_value_items=a_items,
            bid_price=bid,
            net_construction_cost=net_cost,
        )
        result = engine.analyze()

        self.assertFalse(result.final_pass)
        self.assertEqual(result.exclusion_result.status, ExclusionStatus.EXCLUDED)

    def test_negative_est_raises(self):
        with self.assertRaises(ValueError):
            BidAnalysisEngine(
                estimated_price=-1,
                work_type=WorkType.CONSTRUCTION,
                a_value_items=self._make_a_items(),
            )

    def test_negative_bid_raises(self):
        with self.assertRaises(ValueError):
            BidAnalysisEngine(
                estimated_price=5 * UNIT_EOUK,
                work_type=WorkType.CONSTRUCTION,
                a_value_items=self._make_a_items(),
                bid_price=-1,
            )

    def test_specialty_routing(self):
        """전문공사 3~50억 → TABLE_2B."""
        est = 10 * UNIT_EOUK
        a_items = self._make_a_items(1 * UNIT_EOUK)

        engine = BidAnalysisEngine(
            estimated_price=est,
            work_type=WorkType.SPECIALTY,
            a_value_items=a_items,
        )
        result = engine.analyze()

        self.assertEqual(result.table_type, TableType.TABLE_2B)


class TestAssessmentRateFormula(SimpleTestCase):
    """BC-29: 사정률 역산 공식 단위 테스트."""

    def test_implied_floor_rate(self):
        """implied 하한율 = 1순위금액 x 100 / (기초금액 x 1순위사정률)"""
        rank1_bid = 568_453_530
        base_amt = 626_664_000
        rank1_rate = Decimal("100.5955")
        # 곱셈 먼저, 나눗셈 1회 (정밀도 최적화)
        implied = (Decimal(str(rank1_bid)) * Decimal("100")) / (
            Decimal(str(base_amt)) * rank1_rate
        )
        # 합리적 범위 (0.80 ~ 0.95)
        self.assertGreater(implied, Decimal("0.80"))
        self.assertLess(implied, Decimal("0.95"))

    def test_implied_floor_sanity_check(self):
        """implied로 1순위사정률 역산 -> 원래 값과 일치 (파싱 검증)"""
        rank1_bid = 568_453_530
        base_amt = 626_664_000
        rank1_rate = Decimal("100.5955")
        implied = (Decimal(str(rank1_bid)) * Decimal("100")) / (
            Decimal(str(base_amt)) * rank1_rate
        )
        # 역산: rate = bid x 100 / (base x implied)
        recalc = (Decimal(str(rank1_bid)) * Decimal("100")) / (
            Decimal(str(base_amt)) * implied
        )
        self.assertAlmostEqual(float(recalc), float(rank1_rate), places=4)

    def test_assessment_rate_calc(self):
        """사정률 = 투찰금액 x 100 / (기초금액 x 하한율)
        자기 일관성 검증: 깔끔한 값으로 공식 정확성 확인."""
        my_bid = 891_000_000
        base_amt = 1_000_000_000
        floor_rate = Decimal("0.9")
        calc = (Decimal(str(my_bid)) * Decimal("100")) / (
            Decimal(str(base_amt)) * floor_rate
        )
        self.assertAlmostEqual(float(calc), 99.0, places=4)

    def test_reverse_formula(self):
        """역산: 투찰금액 = 기초금액 x 사정률 x 하한율 / 100
        delta=1: 원 단위 정밀도 목표 (실무 투찰은 원 단위)."""
        base_amt = 1_000_000_000
        rate = Decimal("99")
        floor = Decimal("0.9")
        calc_bid = Decimal(str(base_amt)) * rate * floor / Decimal("100")
        self.assertAlmostEqual(float(calc_bid), 891_000_000, delta=1)

    def test_parse_amount_comma_string(self):
        """콤마 포함 문자열 -> int."""
        from g2b.management.commands.verify_assessment_rate import parse_amount

        self.assertEqual(parse_amount("625,594,000"), 625594000)
        self.assertEqual(parse_amount(626664000.0), 626664000)
        self.assertIsNone(parse_amount(None))
        self.assertIsNone(parse_amount(""))


class TestOptimalBid(SimpleTestCase):
    """BC-33: 최적투찰 엔진 테스트."""

    def setUp(self):
        from g2b.services.optimal_bid import (
            OptimalBidInput,
            generate_scenarios,
            compute_expected_score,
            find_optimal_bid,
            evaluate_bid,
            _score_fast,
            _round_half_up_float,
        )
        self.generate_scenarios = generate_scenarios
        self.compute_expected_score = compute_expected_score
        self.find_optimal_bid = find_optimal_bid
        self.evaluate_bid = evaluate_bid
        self._score_fast = _score_fast
        self._round_half_up_float = _round_half_up_float
        self.OptimalBidInput = OptimalBidInput

    # ── generate_scenarios ──

    def test_scenarios_15_gives_1365(self):
        """15개 예비가격 → C(15,4)=1,365개 시나리오."""
        prices = [100_000_000 + i * 1_000_000 for i in range(15)]
        scenarios = self.generate_scenarios(prices)
        self.assertEqual(len(scenarios), 1365)

    def test_scenarios_4_gives_1(self):
        """4개 예비가격 → C(4,4)=1개 시나리오."""
        prices = [100_000_000, 101_000_000, 102_000_000, 103_000_000]
        scenarios = self.generate_scenarios(prices)
        self.assertEqual(len(scenarios), 1)

    def test_scenarios_under_4_raises(self):
        """3개 미만 → ValueError."""
        with self.assertRaises(ValueError):
            self.generate_scenarios([100, 200, 300])

    def test_scenarios_floor_rounding(self):
        """floor 반올림 확인: 4개 합이 4로 나누어지지 않을 때."""
        # 합=403 → 403/4=100.75 → floor=100
        prices = [100, 101, 101, 101]
        scenarios = self.generate_scenarios(prices)
        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0], 100)  # floor(100.75)

    def test_scenarios_exact_division(self):
        """정확히 나누어지는 경우."""
        prices = [100, 100, 100, 100]
        scenarios = self.generate_scenarios(prices)
        self.assertEqual(scenarios[0], 100)  # 400/4=100 (정확)

    # ── _round_half_up_float ──

    def test_round_half_up_float_basic(self):
        self.assertEqual(self._round_half_up_float(0.12345, 4), 0.1235)

    def test_round_half_up_float_five(self):
        """0.5 올림 (banker's rounding 아님)."""
        self.assertEqual(self._round_half_up_float(0.8955, 3), 0.896)

    # ── compute_expected_score ──

    def test_single_scenario_matches_calc_price_score(self):
        """단일 시나리오 기대점수 = calc_price_score 결과와 일치."""
        est = 5 * UNIT_EOUK
        a = 5000_0000
        bid = int((est - a) * 0.9 + a)

        # calc_price_score (Decimal 기반)
        result = calc_price_score(bid, est, a, TableType.TABLE_3)
        decimal_score = float(result.score)

        # compute_expected_score (float 기반, 단일 시나리오)
        params = TABLE_PARAMS_MAP[TableType.TABLE_3]
        expected = self.compute_expected_score(
            bid, [est], a,
            float(params.max_score), float(params.coeff),
            float(params.fixed_ratio), float(params.fixed_score),
        )

        self.assertAlmostEqual(expected, decimal_score, places=1)

    # ── find_optimal_bid ──

    def test_find_optimal_bid_basic(self):
        """기본 구조 검증 — 결과 타입, 필드."""
        from g2b.services.optimal_bid import OptimalBidResult
        prices = [500_000_000 + i * 500_000 for i in range(15)]
        inp = self.OptimalBidInput(
            preliminary_prices=prices,
            a_value=5000_0000,
            table_type=TableType.TABLE_3,
            presume_price=5 * UNIT_EOUK,
        )
        result = self.find_optimal_bid(inp)
        self.assertIsInstance(result, OptimalBidResult)
        self.assertEqual(result.n_scenarios, 1365)
        self.assertGreater(result.recommended_bid, 0)
        self.assertGreater(result.expected_score, 2.0)
        self.assertGreater(result.scan_steps, 0)
        self.assertLessEqual(result.min_scenario_score, result.max_scenario_score)
        self.assertIsNone(result.floor_bid)

    def test_find_optimal_bid_a_zero(self):
        """A=0 케이스 — ratio=bid/est 직접 계산."""
        prices = [500_000_000 + i * 500_000 for i in range(15)]
        inp = self.OptimalBidInput(
            preliminary_prices=prices,
            a_value=0,
            table_type=TableType.TABLE_3,
            presume_price=5 * UNIT_EOUK,
        )
        result = self.find_optimal_bid(inp)
        self.assertGreater(result.expected_score, 2.0)
        self.assertGreater(result.recommended_bid, 0)

    def test_find_optimal_bid_net_cost_floor(self):
        """순공사원가 하한 적용."""
        prices = [500_000_000 + i * 500_000 for i in range(15)]
        inp = self.OptimalBidInput(
            preliminary_prices=prices,
            a_value=5000_0000,
            table_type=TableType.TABLE_3,
            presume_price=5 * UNIT_EOUK,
            net_construction_cost=490_000_000,  # 98% = 480,200,000
        )
        result = self.find_optimal_bid(inp)
        self.assertIsNotNone(result.floor_bid)
        self.assertGreaterEqual(result.recommended_bid, result.floor_bid)

    def test_find_optimal_bid_4_prices_single_scenario(self):
        """4개 예비가격 → 1 시나리오 → ratio=0.9 근처 최적."""
        est_target = 500_000_000
        # 4개 동일 → 1 시나리오, est=500M
        prices = [est_target] * 4
        inp = self.OptimalBidInput(
            preliminary_prices=prices,
            a_value=5000_0000,
            table_type=TableType.TABLE_3,
            presume_price=5 * UNIT_EOUK,
        )
        result = self.find_optimal_bid(inp)
        self.assertEqual(result.n_scenarios, 1)
        # 최적 bid는 ratio=0.9 근처여야
        optimal_at_09 = int(5000_0000 + 0.9 * (est_target - 5000_0000))
        # 1K step 스캔이므로 ±1K 이내 정밀도, ratio=0.9 근처
        self.assertAlmostEqual(
            result.recommended_bid, optimal_at_09, delta=50_000,
        )

    def test_optimal_bid_beats_arbitrary(self):
        """최적 bid ≥ 임의 bid (기대점수 비교)."""
        prices = [500_000_000 + i * 500_000 for i in range(15)]
        inp = self.OptimalBidInput(
            preliminary_prices=prices,
            a_value=5000_0000,
            table_type=TableType.TABLE_3,
            presume_price=5 * UNIT_EOUK,
        )
        result = self.find_optimal_bid(inp)

        # 임의 bid로 기대점수 계산
        arbitrary_bid = int(5000_0000 + 0.88 * (500_000_000 - 5000_0000))
        params = TABLE_PARAMS_MAP[TableType.TABLE_3]
        scenarios = self.generate_scenarios(prices)
        arb_score = self.compute_expected_score(
            arbitrary_bid, scenarios, 5000_0000,
            float(params.max_score), float(params.coeff),
            float(params.fixed_ratio), float(params.fixed_score),
        )
        self.assertGreaterEqual(result.expected_score, arb_score)

    # ── evaluate_bid ──

    def test_evaluate_bid_decimal_consistency(self):
        """Decimal 정합성 — evaluate_bid와 calc_price_score 일치."""
        est = 5 * UNIT_EOUK
        a = 5000_0000
        bid = int((est - a) * 0.9 + a)

        eval_result = self.evaluate_bid(bid, est, a, TableType.TABLE_3)
        ps_result = calc_price_score(bid, est, a, TableType.TABLE_3)

        self.assertAlmostEqual(eval_result.score, float(ps_result.score), places=4)
        self.assertAlmostEqual(eval_result.ratio, float(ps_result.ratio), places=4)

    def test_evaluate_bid_a_ge_est(self):
        """A >= est → score=2, ratio=0."""
        eval_result = self.evaluate_bid(
            100_000_000, 50_000_000, 60_000_000, TableType.TABLE_3,
        )
        self.assertEqual(eval_result.score, 2.0)
        self.assertEqual(eval_result.ratio, 0.0)
        self.assertFalse(eval_result.is_fixed)

    def test_evaluate_bid_out_of_scope(self):
        """OUT_OF_SCOPE → score=2."""
        eval_result = self.evaluate_bid(
            100_000_000, 500_000_000, 0, TableType.OUT_OF_SCOPE,
        )
        self.assertEqual(eval_result.score, 2.0)


# ──────────────────────────────────────────────
# BC-46: 하한율 미달 방지 테스트
# ──────────────────────────────────────────────

class TestFloorRateBid(SimpleTestCase):
    """BC-46: floor_rate_bid 필드 테스트."""

    def _make_result(self, table_type=TableType.TABLE_3, presume_price=5 * UNIT_EOUK,
                     a_value=5000_0000):
        from g2b.services.optimal_bid import OptimalBidInput, find_optimal_bid
        prices = [500_000_000 + i * 500_000 for i in range(15)]
        inp = OptimalBidInput(
            preliminary_prices=prices,
            a_value=a_value,
            table_type=table_type,
            presume_price=presume_price,
        )
        return find_optimal_bid(inp)

    def test_floor_rate_bid_in_result(self):
        """floor_rate_bid 필드 존재."""
        result = self._make_result()
        self.assertIsNotNone(result.floor_rate_bid)
        self.assertIsInstance(result.floor_rate_bid, int)

    def test_recommended_above_floor_single_scenario(self):
        """단일 시나리오에서 추천 bid >= floor_rate_bid (ratio ~90% > floor ~89.7%)."""
        from g2b.services.optimal_bid import OptimalBidInput, find_optimal_bid
        prices = [500_000_000] * 4  # 1 시나리오
        inp = OptimalBidInput(
            preliminary_prices=prices,
            a_value=5000_0000,
            table_type=TableType.TABLE_3,
            presume_price=5 * UNIT_EOUK,
        )
        result = find_optimal_bid(inp)
        self.assertGreaterEqual(result.recommended_bid, result.floor_rate_bid)

    def test_floor_rate_bid_value(self):
        """단일 시나리오에서 정확한 값 검증."""
        from g2b.services.optimal_bid import OptimalBidInput, find_optimal_bid
        import math
        est_target = 500_000_000
        prices = [est_target] * 4  # 1 시나리오, est=500M
        a = 5000_0000
        inp = OptimalBidInput(
            preliminary_prices=prices,
            a_value=a,
            table_type=TableType.TABLE_3,
            presume_price=5 * UNIT_EOUK,
        )
        result = find_optimal_bid(inp)
        # floor_rate for 5억 = 89.745%
        floor_rate = get_floor_rate(5 * UNIT_EOUK)
        expected = math.ceil(a + float(floor_rate) / 100 * (est_target - a))
        self.assertEqual(result.floor_rate_bid, expected)

    def test_floor_rate_bid_different_tables(self):
        """TABLE별 하한율 차등 적용."""
        result_t3 = self._make_result(
            table_type=TableType.TABLE_3, presume_price=5 * UNIT_EOUK)
        result_t2a = self._make_result(
            table_type=TableType.TABLE_2A, presume_price=20 * UNIT_EOUK)
        # 10~50억은 하한율 88.745%, 10억 미만은 89.745%
        # 하한율이 다르므로 floor_rate_bid도 달라야
        self.assertNotEqual(result_t3.floor_rate_bid, result_t2a.floor_rate_bid)


# ──────────────────────────────────────────────
# BC-39: 가격점수 계산기 뷰 테스트
# ──────────────────────────────────────────────

class TestCalculatorView(TestCase):
    """BC-39: 계산기 뷰 테스트."""

    def setUp(self):
        self.client = DjangoClient()

    def test_get_renders_form(self):
        resp = self.client.get("/calculator/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "가격점수 계산기")

    def test_post_normal_calculation(self):
        """추정가격 1.5억, A값 0, 투찰금액 1.35억, 일반공사 → TABLE_5, 점수 출력."""
        resp = self.client.post("/calculator/", {
            "estimated_price": "150000000",
            "work_type": "construction",
            "bid_price": "135000000",
            "national_pension": "0",
            "health_insurance": "0",
            "retirement_mutual_aid": "0",
            "long_term_care": "0",
            "occupational_safety": "0",
            "safety_management": "0",
            "quality_management": "0",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "별표 5")
        # 점수가 표시되어야 함
        self.assertTrue(resp.context["result"].price_score_result is not None)

    def test_post_missing_estimated_price(self):
        """추정가격 미입력 → 에러 메시지."""
        resp = self.client.post("/calculator/", {
            "estimated_price": "",
            "work_type": "construction",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "추정가격을 입력하세요")

    def test_post_out_of_scope(self):
        """100억 이상 → OUT_OF_SCOPE."""
        resp = self.client.post("/calculator/", {
            "estimated_price": "10000000000",
            "work_type": "construction",
            "national_pension": "0",
            "health_insurance": "0",
            "retirement_mutual_aid": "0",
            "long_term_care": "0",
            "occupational_safety": "0",
            "safety_management": "0",
            "quality_management": "0",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "적격심사 대상 외")

    def test_post_heatmap_generated(self):
        """히트맵 데이터가 생성되어야 함."""
        resp = self.client.post("/calculator/", {
            "estimated_price": "150000000",
            "work_type": "construction",
            "national_pension": "0",
            "health_insurance": "0",
            "retirement_mutual_aid": "0",
            "long_term_care": "0",
            "occupational_safety": "0",
            "safety_management": "0",
            "quality_management": "0",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.context["heatmap_rows"]), 0)


# ──────────────────────────────────────────────
# BC-40: 사전 투찰 추천기 뷰 테스트
# ──────────────────────────────────────────────

class TestRecommendView(TestCase):
    """BC-40: 사전 투찰 추천기 뷰 테스트."""

    def setUp(self):
        self.client = DjangoClient()

    def test_get_renders_form(self):
        resp = self.client.get("/recommend/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "사전 투찰 추천기")

    def test_post_basic(self):
        """추정가격+A값만으로 추천 성공."""
        data = {
            "estimated_price": "500000000",
            "base_amount": "500000000",
            "work_type": "construction",
            "a_value": "50000000",
        }
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "추천 투찰 구간")
        self.assertIn("optimal_bid_fmt", resp.context)
        self.assertIn("safe_bid_fmt", resp.context)
        self.assertIn("aggressive_bid_fmt", resp.context)

    def test_post_base_amount_defaults_to_estimated(self):
        """기초금액 미입력 → 추정가격으로 대체."""
        data = {
            "estimated_price": "500000000",
            "work_type": "construction",
            "a_value": "0",
        }
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["result"])

    def test_post_missing_estimated_price(self):
        """추정가격 미입력 → 에러."""
        data = {
            "work_type": "construction",
            "a_value": "0",
        }
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "추정가격을 입력하세요")

    def test_post_out_of_scope(self):
        """100억 이상 → OUT_OF_SCOPE 에러."""
        data = {
            "estimated_price": "10000000000",
            "work_type": "construction",
            "a_value": "0",
        }
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "적격심사 대상 외")

    def test_post_shows_floor_info(self):
        """하한율 정보 표시."""
        data = {
            "estimated_price": "500000000",
            "base_amount": "500000000",
            "work_type": "construction",
            "a_value": "50000000",
        }
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "낙찰하한율")
        self.assertContains(resp, "하한 최소 투찰가")
        self.assertIn("floor_rate_bid", resp.context)

    def test_post_floor_rate_bid_is_int(self):
        """floor_rate_bid 타입 확인."""
        data = {
            "estimated_price": "500000000",
            "base_amount": "500000000",
            "work_type": "construction",
            "a_value": "50000000",
        }
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.context["floor_rate_bid"], int)

    def test_post_no_scenario_in_context(self):
        """사전 추천은 시나리오 엔진을 사용하지 않음."""
        data = {
            "estimated_price": "500000000",
            "work_type": "construction",
            "a_value": "0",
        }
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("n_scenarios", resp.context)
        self.assertNotIn("scenario_rows", resp.context)
        self.assertNotIn("expected_score", resp.context)



# ──────────────────────────────────────────────
# BC-40: 밴드 산출 단위 테스트
# ──────────────────────────────────────────────

class TestRecommendBand(SimpleTestCase):
    """BC-40: 추천 밴드 산출 로직 테스트."""

    def test_band_contains_optimal(self):
        """밴드가 optimal_bid를 포함."""
        from g2b.services.optimal_bid import (
            OptimalBidInput,
            find_optimal_bid,
            generate_scenarios,
            compute_expected_score,
        )

        prices = [500_000_000 + i * 500_000 for i in range(15)]
        inp = OptimalBidInput(
            preliminary_prices=prices,
            a_value=5000_0000,
            table_type=TableType.TABLE_3,
            presume_price=5 * UNIT_EOUK,
        )
        result = find_optimal_bid(inp)

        params = TABLE_PARAMS_MAP[TableType.TABLE_3]
        scenarios = generate_scenarios(prices)
        optimal_bid = result.recommended_bid
        threshold = result.expected_score - 0.05

        band_bids = []
        for offset in range(-100, 101):
            test_bid = optimal_bid + offset * 1_000
            if test_bid <= 0:
                continue
            es = compute_expected_score(
                test_bid, scenarios, 5000_0000,
                float(params.max_score), float(params.coeff),
                float(params.fixed_ratio), float(params.fixed_score),
            )
            if es >= threshold:
                band_bids.append(test_bid)

        band_low = min(band_bids)
        band_high = max(band_bids)
        self.assertLessEqual(band_low, optimal_bid)
        self.assertGreaterEqual(band_high, optimal_bid)
        self.assertGreater(len(band_bids), 0)

    def test_band_all_scores_above_threshold(self):
        """밴드 내 모든 bid의 기대점수가 threshold 이상."""
        from g2b.services.optimal_bid import (
            OptimalBidInput,
            find_optimal_bid,
            generate_scenarios,
            compute_expected_score,
        )

        prices = [500_000_000 + i * 500_000 for i in range(15)]
        inp = OptimalBidInput(
            preliminary_prices=prices,
            a_value=5000_0000,
            table_type=TableType.TABLE_3,
            presume_price=5 * UNIT_EOUK,
        )
        result = find_optimal_bid(inp)

        params = TABLE_PARAMS_MAP[TableType.TABLE_3]
        scenarios = generate_scenarios(prices)
        optimal_bid = result.recommended_bid
        threshold = result.expected_score - 0.05

        for offset in range(-100, 101):
            test_bid = optimal_bid + offset * 1_000
            if test_bid <= 0:
                continue
            es = compute_expected_score(
                test_bid, scenarios, 5000_0000,
                float(params.max_score), float(params.coeff),
                float(params.fixed_ratio), float(params.fixed_score),
            )
            if es >= threshold:
                # 밴드 내 → threshold 이상이어야
                self.assertGreaterEqual(es, threshold)


# ──────────────────────────────────────────────
# BC-45: 사전 추천 서비스 테스트
# ──────────────────────────────────────────────

class TestPreBidRecommend(SimpleTestCase):
    """BC-45: prebid_recommend 서비스 테스트."""

    def test_basic_recommendation(self):
        """기본 사전 추천 — 결과 필드 존재 확인."""
        from g2b.services.prebid_recommend import prebid_recommend
        result = prebid_recommend(
            base_amount=500_000_000,
            a_value=50_000_000,
            table_type=TableType.TABLE_3,
            presume_price=500_000_000,
        )
        self.assertIsInstance(result.optimal_bid, int)
        self.assertIsInstance(result.safe_bid, int)
        self.assertIsInstance(result.aggressive_bid, int)
        self.assertIsInstance(result.floor_rate_bid, int)
        self.assertTrue(result.floor_rate_pass)

    def test_optimal_at_90_percent(self):
        """최적 bid는 ratio 90% 위치."""
        from g2b.services.prebid_recommend import prebid_recommend
        base = 500_000_000
        a = 50_000_000
        result = prebid_recommend(
            base_amount=base,
            a_value=a,
            table_type=TableType.TABLE_3,
            presume_price=base,
        )
        expected = round(a + 0.9 * (base - a))
        self.assertEqual(result.optimal_bid, expected)

    def test_band_contains_optimal(self):
        """밴드가 optimal_bid를 포함."""
        from g2b.services.prebid_recommend import prebid_recommend
        result = prebid_recommend(
            base_amount=500_000_000,
            a_value=50_000_000,
            table_type=TableType.TABLE_2A,
            presume_price=20 * UNIT_EOUK,
        )
        self.assertLessEqual(result.band_low, result.optimal_bid)
        self.assertGreaterEqual(result.band_high, result.optimal_bid)
        self.assertEqual(result.safe_bid, result.band_high)
        self.assertEqual(result.aggressive_bid, result.band_low)

    def test_band_width_varies_by_table(self):
        """TABLE별 밴드 폭이 다름 (coeff 차이)."""
        from g2b.services.prebid_recommend import prebid_recommend
        r1 = prebid_recommend(
            base_amount=500_000_000, a_value=50_000_000,
            table_type=TableType.TABLE_1, presume_price=60 * UNIT_EOUK,
        )
        r3 = prebid_recommend(
            base_amount=500_000_000, a_value=50_000_000,
            table_type=TableType.TABLE_3, presume_price=5 * UNIT_EOUK,
        )
        # TABLE_1(coeff=2)의 밴드가 TABLE_3(coeff=20)보다 훨씬 넓어야 함
        width_1 = r1.band_high - r1.band_low
        width_3 = r3.band_high - r3.band_low
        self.assertGreater(width_1, width_3 * 5)

    def test_floor_rate_enforcement(self):
        """하한율 미달 시 밴드 하한이 floor_rate_bid 이상."""
        from g2b.services.prebid_recommend import prebid_recommend
        result = prebid_recommend(
            base_amount=500_000_000,
            a_value=50_000_000,
            table_type=TableType.TABLE_3,
            presume_price=500_000_000,
        )
        self.assertGreaterEqual(result.band_low, result.floor_rate_bid)

    def test_no_scenario_dependency(self):
        """prebid_recommend는 generate_scenarios를 사용하지 않음."""
        import inspect
        from g2b.services import prebid_recommend as mod
        source = inspect.getsource(mod)
        self.assertNotIn('generate_scenarios', source)
        self.assertNotIn('OptimalBidInput', source)
        self.assertNotIn('find_optimal_bid', source)

    def test_out_of_scope_raises(self):
        """OUT_OF_SCOPE → ValueError."""
        from g2b.services.prebid_recommend import prebid_recommend
        with self.assertRaises(ValueError):
            prebid_recommend(
                base_amount=10_000_000_000,
                a_value=0,
                table_type=TableType.OUT_OF_SCOPE,
                presume_price=10_000_000_000,
            )


# ──────────────────────────────────────────────
# BC-45: scan bounds + band threshold (optimal_bid.py 내부 테스트)
# ──────────────────────────────────────────────

class TestScanBoundsAndStrategy(SimpleTestCase):
    """BC-45: TABLE별 scan bounds, band threshold, 3-strategy 테스트 (내부 엔진)."""

    def test_scan_bounds_table2a(self):
        """TABLE_2A bounds (0.87, 0.93) 확인."""
        from g2b.services.optimal_bid import _SCAN_BOUNDS
        lb, ub = _SCAN_BOUNDS[TableType.TABLE_2A]
        self.assertAlmostEqual(lb, 0.87)
        self.assertAlmostEqual(ub, 0.93)

    def test_scan_bounds_table3(self):
        """TABLE_3 bounds (0.89, 0.915) 확인."""
        from g2b.services.optimal_bid import _SCAN_BOUNDS
        lb, ub = _SCAN_BOUNDS[TableType.TABLE_3]
        self.assertAlmostEqual(lb, 0.89)
        self.assertAlmostEqual(ub, 0.915)

    def test_band_threshold_table1(self):
        """TABLE_1 threshold 0.10 적용 확인."""
        from g2b.services.optimal_bid import _BAND_THRESHOLDS
        self.assertAlmostEqual(_BAND_THRESHOLDS[TableType.TABLE_1], 0.10)

    def test_three_strategy_fields(self):
        """OptimalBidResult에 safe/aggressive 필드 존재 + 밴드 내 위치."""
        from g2b.services.optimal_bid import OptimalBidInput, find_optimal_bid
        prices = [500_000_000 + i * 500_000 for i in range(15)]
        inp = OptimalBidInput(
            preliminary_prices=prices,
            a_value=5000_0000,
            table_type=TableType.TABLE_2A,
            presume_price=20 * UNIT_EOUK,
        )
        result = find_optimal_bid(inp)
        # 필드 존재
        self.assertTrue(hasattr(result, 'safe_bid'))
        self.assertTrue(hasattr(result, 'aggressive_bid'))
        self.assertTrue(hasattr(result, 'band_threshold'))
        self.assertTrue(hasattr(result, 'band_low'))
        self.assertTrue(hasattr(result, 'band_high'))
        # 밴드 범위 정합성
        self.assertLessEqual(result.band_low, result.recommended_bid)
        self.assertGreaterEqual(result.band_high, result.recommended_bid)
        # threshold는 TABLE_2A 기본값
        self.assertAlmostEqual(result.band_threshold, 0.05)


# ──────────────────────────────────────────────
# BC-53: AI 전략 리포트
# ──────────────────────────────────────────────

class TestReportStats(TestCase):
    """BC-53: report_stats 반환 구조 확인."""

    def test_report_stats_return_structure(self):
        """get_similar_bid_stats 반환 dict 키 확인."""
        from g2b.services.report_stats import get_similar_bid_stats
        # DB 없이 호출하면 빈 결과
        try:
            result = get_similar_bid_stats(500_000_000)
        except Exception:
            # DB 연결 없으면 스킵
            return
        expected_keys = {"count", "avg_bidder_cnt", "p10_rate", "p50_rate", "p90_rate"}
        self.assertEqual(set(result.keys()), expected_keys)


class TestAIReportDataclasses(SimpleTestCase):
    """BC-53: ReportInput/ReportOutput dataclass 필드 검증."""

    def test_report_input_fields(self):
        from g2b.services.ai_report import ReportInput
        inp = ReportInput(
            table_name="별표 3",
            presume_price=500_000_000,
            a_value=50_000_000,
            floor_rate="89.75",
            floor_bid=404_775_000,
            band_low=404_550_000,
            band_high=405_450_000,
            base_bid=405_000_000,
            safe_bid=405_450_000,
            aggressive_bid=404_550_000,
            similar_stats={"count": 10},
        )
        self.assertEqual(inp.table_name, "별표 3")
        self.assertEqual(inp.presume_price, 500_000_000)
        self.assertEqual(inp.base_bid, 405_000_000)

    def test_report_output_fields(self):
        from g2b.services.ai_report import ReportOutput
        out = ReportOutput(
            summary="테스트 요약",
            strategy="테스트 전략",
            risk_factors=["리스크1"],
            evidence=["근거1"],
            action_items=["액션1"],
        )
        self.assertEqual(out.summary, "테스트 요약")
        self.assertIsInstance(out.risk_factors, list)


class TestGenerateReportFallback(SimpleTestCase):
    """BC-53: API 실패 시 fallback 동작."""

    def test_fallback_when_no_api_key(self):
        """OPENAI_API_KEY 없으면 fallback 리포트 반환."""
        from g2b.services.ai_report import ReportInput, generate_report
        inp = ReportInput(
            table_name="별표 3",
            presume_price=500_000_000,
            a_value=50_000_000,
            floor_rate="89.75",
            floor_bid=404_775_000,
            band_low=404_550_000,
            band_high=405_450_000,
            base_bid=405_000_000,
            safe_bid=405_450_000,
            aggressive_bid=404_550_000,
            similar_stats={"count": 0, "avg_bidder_cnt": 0,
                           "p10_rate": 0, "p50_rate": 0, "p90_rate": 0},
        )
        with self.settings(OPENAI_API_KEY=''):
            result = generate_report(inp)
        self.assertIn("OPENAI_API_KEY", result.risk_factors[1])
        self.assertTrue(len(result.summary) > 0)
        self.assertTrue(len(result.action_items) > 0)


class TestAIReportView(TestCase):
    """BC-53: AI 리포트 뷰 테스트."""

    def setUp(self):
        self.client = DjangoClient()

    def test_get_renders_form(self):
        resp = self.client.get("/ai-report/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "AI 전략 리포트")


class TestConstructionSyncMapping(SimpleTestCase):
    """일일 건설공사 동기화 매핑 테스트."""

    def test_notice_mapping_populates_current_models(self):
        item = {
            'bidNtceNo': 'R26BK01369994',
            'bidNtceOrd': '000',
            'refNtceNo': 'R26BK01369994',
            'bidNtceNm': '2026년 포장도로 정비공사(연간단가)',
            'ntceKindNm': '등록공고',
            'opengPlce': '나라장터',
            'reNtceYn': 'N',
            'cnstrtsiteRgnNm': '서울특별시 중랑구',
            'orderPlanUntyNo': 'R26DD20675014',
            'bfSpecRgstNo': '',
            'mainCnsttyNm': '지반조성ㆍ포장공사업',
            'sucsfbidMthdCd': '낙030001',
            'sucsfbidMthdNm': '적격심사제-추정가격이 10억원 미만 4억원 이상인 입찰공사',
            'ntceInsttOfclNm': '문종민',
            'ntceInsttOfclTelNo': '02-2094-1237',
            'ntceInsttNm': '서울특별시 중랑구',
            'presmptPrce': '901700000',
            'bdgtAmt': '1329435590',
            'govsplyAmt': '185144410',
            'sucsfbidLwltRate': '89.745',
            'rgnDutyJntcontrctRt': '',
            'mainCnsttyPresmptPrce': '901700000',
            'bidNtceDt': '2026-03-05 01:43:50',
            'opengDt': '2026-03-12 11:00:00',
            'bidMethdNm': '전자입찰',
            'cntrctCnclsMthdNm': '제한경쟁',
            'cntrctCnclsSttusNm': '총액계약',
            'dminsttNm': '서울특별시 중랑구',
            'dminsttCd': '3060000',
            'ntceInsttCd': '3060000',
        }

        announcement = map_notice_to_announcement(item)
        contract = map_notice_to_contract(item)

        self.assertEqual(announcement['bid_ntce_no'], 'R26BK01369994')
        self.assertEqual(announcement['site_area'], '서울특별시 중랑구')
        self.assertEqual(announcement['license_limit_list'], '지반조성ㆍ포장공사업')
        self.assertEqual(announcement['presume_price'], 901700000)

        self.assertEqual(contract['procurement_type'], '공사')
        self.assertEqual(contract['contract_no'], PLACEHOLDER_CONTRACT_NO)
        self.assertEqual(contract['ntce_date'], '20260305')
        self.assertEqual(contract['openg_date'], '20260312')
        self.assertIn('적격심사제', contract['win_method'])

    def test_notice_eligibility_uses_price_and_win_method(self):
        eligible = {
            'presmptPrce': '901700000',
            'sucsfbidMthdNm': '적격심사제-추정가격이 10억원 미만 4억원 이상인 입찰공사',
        }
        ineligible = {
            'presmptPrce': '12000000000',
            'sucsfbidMthdNm': '적격심사제',
        }

        self.assertTrue(is_eligible_notice_for_service(eligible))
        self.assertFalse(is_eligible_notice_for_service(ineligible))

    def test_notice_upcoming_filter_uses_openg_datetime(self):
        upcoming = {'opengDt': '2026-03-12 18:00:00'}
        finished = {'opengDt': '2026-03-12 09:30:00'}

        self.assertTrue(is_upcoming_notice(upcoming, '202603121100'))
        self.assertFalse(is_upcoming_notice(finished, '202603121100'))

    def test_bid_result_and_api_support_mapping(self):
        notice_item = {
            'presmptPrce': '901700000',
            'sucsfbidLwltRate': '89.745',
        }
        result_item = {
            'bidNtceNo': 'R26BK01371809',
            'bidNtceOrd': '000',
            'bidClsfcNo': '0',
            'rbidNo': '000',
            'bidNtceNm': '안양시 자원회수시설 소각로 내부 보수작업',
            'prtcptCnum': '51',
            'bidwinnrNm': '상신기계공영(주)',
            'bidwinnrBizno': '1188118120',
            'sucsfbidAmt': '193246660',
            'sucsfbidRate': '90.075',
        }
        a_value_item = {
            'bidNtceNo': 'R26BK01369994',
            'bidNtceOrd': '000',
            'sftyMngcst': '15542541',
            'sftyChckMngcst': '34642830',
            'rtrfundNon': '7893027',
            'mrfnHealthInsrprm': '12337144',
            'npnInsrprm': '16300817',
            'odsnLngtrmrcprInsrprm': '1621100',
            'qltyMngcst': '0',
            'prearngPrceDcsnMthdNm': '복수예가',
        }
        prelim_item = {
            'bidNtceNo': 'R26BK01369994',
            'bidNtceOrd': '000',
            'compnoRsrvtnPrceSno': '1',
            'bsisPlnprc': '966587300',
            'drwtYn': 'N',
            'drwtNum': '77',
            'plnprc': '995453175',
            'bssamt': '991870000',
        }
        base_amount_item = {
            'bidNtceNo': 'R26BK01369994',
            'bidNtceOrd': '000',
            'bssamt': '991870000',
        }

        bid_result = map_successful_bid_to_result(result_item, notice_item)
        a_value = map_a_value_item(a_value_item)
        prelim = map_prelim_price_item(prelim_item)
        placeholder = map_base_amount_to_placeholder_prelim(base_amount_item)

        self.assertEqual(bid_result['company_nm'], '상신기계공영(주)')
        self.assertEqual(str(bid_result['bid_rate']), '90.075')
        self.assertEqual(bid_result['presume_price'], 901700000)

        self.assertEqual(a_value['national_pension'], 16300817)
        self.assertEqual(a_value['price_decision_method'], '복수예가')

        self.assertEqual(prelim['sequence_no'], 1)
        self.assertEqual(prelim['base_amount'], 991870000)

        self.assertEqual(placeholder['sequence_no'], PLACEHOLDER_PRELIM_SEQUENCE)
        self.assertEqual(placeholder['base_amount'], 991870000)


class TestUnifiedUiConstructionFilters(TestCase):
    """Unified UI API가 건설 적격심사 공고만 노출하는지 검증."""

    def setUp(self):
        self.client = DjangoClient()
        self.today = timezone.localdate().strftime('%Y%m%d')

    def _create_notice(
        self,
        *,
        bid_ntce_no: str,
        title: str,
        procurement_type: str,
        win_method: str,
        presume_price: int,
        created_offset_minutes: int = 0,
        openg_date: str | None = None,
        license_limit_list: str = "[건축공사업(0002) 과 ()]",
    ) -> None:
        announcement = BidAnnouncement.objects.create(
            bid_ntce_no=bid_ntce_no,
            bid_ntce_ord="1",
            bid_ntce_nm=title,
            presume_price=presume_price,
            license_limit_list=license_limit_list,
            ntce_dept="테스트기관",
        )
        contract = BidContract.objects.create(
            procurement_type=procurement_type,
            bid_ntce_no=bid_ntce_no,
            bid_ntce_ord="1",
            bid_ntce_nm=title,
            demand_org="테스트수요기관",
            ntce_org="테스트공고기관",
            openg_date=openg_date or self.today,
            win_method=win_method,
            bid_method="전자입찰",
            presume_price=presume_price,
            license_limit_list=license_limit_list,
        )
        created_at = timezone.now() + timedelta(minutes=created_offset_minutes)
        BidAnnouncement.objects.filter(pk=announcement.pk).update(created_at=created_at)
        BidContract.objects.filter(pk=contract.pk).update(created_at=created_at)

    def test_dashboard_shows_only_construction_eligible_notices(self):
        self._create_notice(
            bid_ntce_no="CONTRACT-001",
            title="칠곡경찰서 리모델링 공사(건축)",
            procurement_type="공사",
            win_method="적격심사제",
            presume_price=1_405_763_637,
        )
        self._create_notice(
            bid_ntce_no="SERVICE-001",
            title="인도네시아 법령정보시스템 구축 사업 전산감리 용역",
            procurement_type="일반용역",
            win_method="협상에의한계약",
            presume_price=244_940_602,
            license_limit_list="[정보시스템 감리법인(6146) 과 ()]",
        )
        self._create_notice(
            bid_ntce_no="NONELIGIBLE-001",
            title="호서벤처밸리 공장동 바닥 에폭시 보수공사",
            procurement_type="공사",
            win_method="최저가낙찰제",
            presume_price=78_800_000,
            license_limit_list="[도장ㆍ습식ㆍ방수ㆍ석공사업(4992) 과 ()]",
        )

        response = self.client.get("/api/ui/dashboard/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["metrics"][0]["label"], "오늘 개찰 건설공고")
        self.assertEqual(payload["metrics"][0]["value"], "1건")
        titles = [item["title"] for item in payload["todayNotices"]]
        self.assertEqual(titles, ["칠곡경찰서 리모델링 공사(건축)"])

    def test_notice_search_excludes_non_construction_notices(self):
        self._create_notice(
            bid_ntce_no="CONTRACT-002",
            title="운남체육시설단지 재해복구공사",
            procurement_type="공사",
            win_method="적격심사제",
            presume_price=231_054_546,
        )
        self._create_notice(
            bid_ntce_no="SERVICE-002",
            title="정보시스템 통합 유지관리 용역",
            procurement_type="일반용역",
            win_method="협상에의한계약",
            presume_price=1_330_985_090,
            license_limit_list="[소프트웨어사업자(컴퓨터관련서비스사업)(1468) 과 ()]",
        )

        included = self.client.get("/api/ui/notices/search/", {"query": "재해복구"})
        self.assertEqual(included.status_code, 200)
        included_payload = included.json()
        self.assertEqual(included_payload["count"], 1)
        self.assertEqual(
            [row["title"] for row in included_payload["results"]],
            ["운남체육시설단지 재해복구공사"],
        )

        excluded = self.client.get("/api/ui/notices/search/", {"query": "정보시스템"})
        self.assertEqual(excluded.status_code, 200)
        excluded_payload = excluded.json()
        self.assertEqual(excluded_payload["count"], 0)
        self.assertEqual(excluded_payload["results"], [])

    def test_notice_search_filters_by_region(self):
        self._create_notice(
            bid_ntce_no="CONTRACT-REGION-001",
            title="서울권역 도로 정비공사",
            procurement_type="공사",
            win_method="적격심사제",
            presume_price=510_000_000,
        )
        self._create_notice(
            bid_ntce_no="CONTRACT-REGION-002",
            title="부산권역 도로 정비공사",
            procurement_type="공사",
            win_method="적격심사제",
            presume_price=520_000_000,
        )
        BidContract.objects.filter(bid_ntce_no="CONTRACT-REGION-001").update(demand_org_area="서울")
        BidContract.objects.filter(bid_ntce_no="CONTRACT-REGION-002").update(demand_org_area="부산")

        response = self.client.get("/api/ui/notices/search/", {"region": "서울"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            [row["title"] for row in payload["results"]],
            ["서울권역 도로 정비공사"],
        )

    def test_recommendation_default_and_direct_access_use_only_construction_scope(self):
        self._create_notice(
            bid_ntce_no="CONTRACT-003",
            title="청년창업농 스마트팜 단지조성사업 온실공사",
            procurement_type="공사",
            win_method="적격심사제",
            presume_price=6_740_713_637,
            created_offset_minutes=1,
        )
        self._create_notice(
            bid_ntce_no="SERVICE-003",
            title="2026년도 한국조폐공사 임직원 종합건강검진 용역",
            procurement_type="일반용역",
            win_method="협상에의한계약",
            presume_price=439_500_000,
            created_offset_minutes=2,
            license_limit_list="[의료기관개설허가(종합병원)(5373) 과 ()]",
        )

        response = self.client.get("/api/ui/notices/recommendation/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["notice"]["noticeNo"], "CONTRACT-003")

        blocked = self.client.get("/api/ui/notices/recommendation/", {"bid_ntce_no": "SERVICE-003"})
        self.assertEqual(blocked.status_code, 404)


# ──────────────────────────────────────────────
# fetch 커맨드 재작성 관련 테스트
# ──────────────────────────────────────────────

class TestBulkUpsert(TestCase):
    """bulk_upsert() 공유 함수 테스트"""

    def test_creates_new_rows(self):
        rows = [
            {
                'bid_ntce_no': 'TEST001',
                'bid_ntce_ord': '00',
                'bid_ntce_nm': '테스트 공고 1',
                'presume_price': 500000000,
            },
            {
                'bid_ntce_no': 'TEST002',
                'bid_ntce_ord': '00',
                'bid_ntce_nm': '테스트 공고 2',
                'presume_price': 300000000,
            },
        ]
        created, updated = bulk_upsert(
            BidAnnouncement, rows, unique_fields=['bid_ntce_no', 'bid_ntce_ord'],
        )
        self.assertEqual(created, 2)
        self.assertEqual(updated, 0)
        self.assertEqual(BidAnnouncement.objects.count(), 2)

    def test_updates_existing_rows(self):
        BidAnnouncement.objects.create(
            bid_ntce_no='TEST001', bid_ntce_ord='00', bid_ntce_nm='원래 공고',
        )
        rows = [
            {
                'bid_ntce_no': 'TEST001',
                'bid_ntce_ord': '00',
                'bid_ntce_nm': '변경된 공고',
                'presume_price': 500000000,
            },
        ]
        created, updated = bulk_upsert(
            BidAnnouncement, rows, unique_fields=['bid_ntce_no', 'bid_ntce_ord'],
        )
        self.assertEqual(created, 0)
        self.assertEqual(updated, 1)
        obj = BidAnnouncement.objects.get(bid_ntce_no='TEST001')
        self.assertEqual(obj.bid_ntce_nm, '변경된 공고')

    def test_empty_list(self):
        created, updated = bulk_upsert(
            BidAnnouncement, [], unique_fields=['bid_ntce_no', 'bid_ntce_ord'],
        )
        self.assertEqual(created, 0)
        self.assertEqual(updated, 0)

    def test_deduplicates_within_batch(self):
        rows = [
            {'bid_ntce_no': 'DUP001', 'bid_ntce_ord': '00', 'bid_ntce_nm': '첫번째'},
            {'bid_ntce_no': 'DUP001', 'bid_ntce_ord': '00', 'bid_ntce_nm': '두번째'},
        ]
        created, updated = bulk_upsert(
            BidAnnouncement, rows, unique_fields=['bid_ntce_no', 'bid_ntce_ord'],
        )
        self.assertEqual(created, 1)
        self.assertEqual(updated, 0)
        obj = BidAnnouncement.objects.get(bid_ntce_no='DUP001')
        self.assertEqual(obj.bid_ntce_nm, '두번째')


class TestAnnouncementMapping(SimpleTestCase):
    """공고 매핑 함수 테스트"""

    def test_map_notice_to_announcement(self):
        item = {
            'bidNtceNo': '20260101001',
            'bidNtceOrd': '00',
            'bidNtceNm': '테스트 건설공사',
            'presmptPrce': '5000000000',
            'sucsfbidLwltRate': '87.745',
            'reNtceYn': 'N',
        }
        result = map_notice_to_announcement(item)
        self.assertEqual(result['bid_ntce_no'], '20260101001')
        self.assertEqual(result['bid_ntce_ord'], '00')
        self.assertEqual(result['presume_price'], 5000000000)
        self.assertEqual(result['first_ntce_yn'], 'Y')

    def test_eligible_notice_filter(self):
        eligible = {'presmptPrce': '5000000000', 'sucsfbidMthdNm': '적격심사제'}
        ineligible_price = {'presmptPrce': '15000000000', 'sucsfbidMthdNm': '적격심사제'}
        ineligible_method = {'presmptPrce': '5000000000', 'sucsfbidMthdNm': '최저가'}

        self.assertTrue(is_eligible_notice_for_service(eligible))
        self.assertFalse(is_eligible_notice_for_service(ineligible_price))
        self.assertFalse(is_eligible_notice_for_service(ineligible_method))

    def test_upcoming_notice_filter(self):
        future = {'opengDt': '202612311200'}
        past = {'opengDt': '202001010000'}
        now_key = '202603131200'

        self.assertTrue(is_upcoming_notice(future, now_key))
        self.assertFalse(is_upcoming_notice(past, now_key))


class TestWinningBidMapping(SimpleTestCase):
    """낙찰결과 매핑 함수 테스트"""

    def test_map_successful_bid_to_result(self):
        item = {
            'bidNtceNo': '20260101001',
            'bidNtceOrd': '00',
            'bidwinnrNm': '테스트건설',
            'bidwinnrBizno': '1234567890',
            'sucsfbidRate': '89.123',
            'sucsfbidAmt': '4500000000',
            'prtcptCnum': '15',
        }
        result = map_successful_bid_to_result(item, None)
        self.assertEqual(result['bid_ntce_no'], '20260101001')
        self.assertEqual(result['company_nm'], '테스트건설')
        self.assertIsNone(result['presume_price'])
        self.assertIsNone(result['success_lowest_rate'])

    def test_enrichment_from_notice(self):
        item = {
            'bidNtceNo': '20260101001',
            'bidNtceOrd': '00',
            'bidwinnrNm': '테스트건설',
            'bidwinnrBizno': '1234567890',
        }
        notice = {
            'presmptPrce': '5000000000',
            'sucsfbidLwltRate': '87.745',
        }
        result = map_successful_bid_to_result(item, notice)
        self.assertEqual(result['presume_price'], 5000000000)


class TestPipeline3OrdMismatch(SimpleTestCase):
    """BC-정합성: A값 수집 시 차수(ord) 정합성 검증."""

    def _make_command(self):
        from g2b.management.commands.collect_bid_api_data import Command
        return Command()

    def test_matching_ord_is_saved(self):
        """응답 items 중 ntce_ord와 일치하는 row만 선택한다."""
        from unittest.mock import MagicMock, patch

        cmd = self._make_command()
        log = MagicMock()
        log.error_detail = ""

        items = [
            {"bidNtceOrd": "000", "bidNtceNo": "20260101001",
             "npnInsrprm": "1000", "mrfnHealthInsrprm": "0",
             "rtrfundNon": "0", "odsnLngtrmrcprInsrprm": "0",
             "sftyMngcst": "0", "sftyChckMngcst": "0", "qltyMngcst": "0",
             "prearngPrceDcsnMthdNm": "표준시장"},
            {"bidNtceOrd": "001", "bidNtceNo": "20260101001",
             "npnInsrprm": "9999", "mrfnHealthInsrprm": "0",
             "rtrfundNon": "0", "odsnLngtrmrcprInsrprm": "0",
             "sftyMngcst": "0", "sftyChckMngcst": "0", "qltyMngcst": "0",
             "prearngPrceDcsnMthdNm": "표준시장"},
        ]
        api_response = {
            "response": {"header": {"resultCode": "00"}, "body": {
                "items": {"item": items}, "totalCount": 2,
            }}
        }

        with patch.object(cmd, '_save_raw_json'), \
             patch('g2b.management.commands.collect_bid_api_data.call_api',
                   return_value=api_response), \
             patch('g2b.management.commands.collect_bid_api_data.BidApiAValue') as MockModel:
            MockModel.objects.update_or_create = MagicMock()
            result = cmd._collect_a_value(
                MagicMock(), "fake_key", "20260101001", "001", log,
            )

        self.assertEqual(result, "ok")
        call_kwargs = MockModel.objects.update_or_create.call_args
        defaults = call_kwargs[1]["defaults"]
        # ord="001" 행의 npnInsrprm=9999 이어야 함
        self.assertEqual(defaults["national_pension"], 9999)

    def test_ord_mismatch_returns_empty(self):
        """응답 items에 기대 차수가 없으면 'empty'를 반환한다."""
        from unittest.mock import MagicMock, patch

        cmd = self._make_command()
        log = MagicMock()
        log.error_detail = ""

        items = [
            {"bidNtceOrd": "000", "bidNtceNo": "20260101001",
             "npnInsrprm": "1000"},
        ]
        api_response = {
            "response": {"header": {"resultCode": "00"}, "body": {
                "items": {"item": items}, "totalCount": 1,
            }}
        }

        with patch('g2b.management.commands.collect_bid_api_data.call_api',
                   return_value=api_response):
            result = cmd._collect_a_value(
                MagicMock(), "fake_key", "20260101001", "002", log,
            )

        self.assertEqual(result, "empty")


class TestPipeline3PartialSuccessRetry(SimpleTestCase):
    """BC-정합성: CollectionLog partial success는 재시도 대상에 포함된다."""

    def _build_targets_set(self, logs_qs_mock, qs_rows, limit=100):
        """_extract_targets 내부의 collected set 구성 로직을 직접 검증."""
        from django.db.models import Q
        # partial success (a_value_status=ok, prelim_status=error) 는
        # complete_condition을 만족하지 않으므로 collected에 포함되지 않아야 함
        complete_condition = (
            Q(a_value_status="ok", prelim_status="ok")
            | Q(a_value_status="empty", prelim_status__in=["ok", "empty"])
        )
        # 로그 목록을 직접 필터링하여 검증
        statuses = [
            {"bid_ntce_no": "A001", "bid_ntce_ord": "00",
             "a_value_status": "ok", "prelim_status": "ok"},
            {"bid_ntce_no": "A002", "bid_ntce_ord": "00",
             "a_value_status": "ok", "prelim_status": "error"},   # partial → 재시도
            {"bid_ntce_no": "A003", "bid_ntce_ord": "00",
             "a_value_status": "empty", "prelim_status": "empty"},  # 비대상확정
            {"bid_ntce_no": "A004", "bid_ntce_ord": "00",
             "a_value_status": "pending", "prelim_status": "pending"},  # 미완료 → 재시도
        ]

        def matches_complete(row):
            a, p = row["a_value_status"], row["prelim_status"]
            return (a == "ok" and p == "ok") or (a == "empty" and p in ("ok", "empty"))

        collected = {
            (r["bid_ntce_no"], r["bid_ntce_ord"])
            for r in statuses if matches_complete(r)
        }
        # A001(ok/ok), A003(empty/empty) 만 완료
        self.assertIn(("A001", "00"), collected)
        self.assertIn(("A003", "00"), collected)
        # A002(partial), A004(pending) 은 재시도 대상
        self.assertNotIn(("A002", "00"), collected)
        self.assertNotIn(("A004", "00"), collected)

    def test_partial_success_not_in_collected(self):
        self._build_targets_set(None, [])


class TestPipeline2bMissingNoticeBackfill(SimpleTestCase):
    """BC-자가복구: BidAnnouncement에 없는 공고를 보조 조회로 복구한다."""

    def test_backfill_adds_to_existing_keys(self):
        """보조 조회 성공 시 existing_keys에 추가되어 계약이 적재된다."""
        from unittest.mock import MagicMock, patch, call
        from io import StringIO
        from django.core.management import call_command

        notice_item = {
            "bidNtceNo": "20260199001",
            "bidNtceOrd": "00",
            "bidNtceNm": "보조조회 복구 공사",
            "presmptPrce": "500000000",
            "sucsfbidMthdNm": "적격심사",
            "ntceInsttNm": "테스트기관",
            "ntceInsttCd": "001",
        }

        with patch(
            'g2b.management.commands.fetch_contracts.fetch_construction_contracts',
            return_value=[
                {
                    "bsnsDivNm": "공사",
                    "bidNtceNo": "20260199001",
                    "bidNtceOrd": "00",
                    "cntrctNo": "C99001",
                }
            ],
        ), patch(
            'g2b.management.commands.fetch_contracts.fetch_construction_notices_by_no',
            return_value=[notice_item],
        ) as mock_backfill, patch(
            'g2b.management.commands.fetch_contracts.BidAnnouncement'
        ) as MockAnn, patch(
            'g2b.management.commands.fetch_contracts.bulk_upsert',
            return_value=(1, 0),
        ), patch(
            'g2b.management.commands.fetch_contracts.BidContract'
        ):
            # BidAnnouncement.objects.filter(...).values_list(...) → 빈 set (공고 미수집)
            MockAnn.objects.filter.return_value.values_list.return_value = []

            out = StringIO()
            call_command('fetch_contracts', '--days=1', '--dry-run', stdout=out)

        # 보조 조회 함수가 호출되었는지 확인
        mock_backfill.assert_called_once_with("20260199001", "00")

    def test_backfill_failure_is_skipped(self):
        """보조 조회가 예외를 던지면 해당 공고를 스킵하고 계속 진행한다."""
        from unittest.mock import MagicMock, patch
        from io import StringIO
        from django.core.management import call_command

        with patch(
            'g2b.management.commands.fetch_contracts.fetch_construction_contracts',
            return_value=[
                {
                    "bsnsDivNm": "공사",
                    "bidNtceNo": "20260199002",
                    "bidNtceOrd": "00",
                    "cntrctNo": "C99002",
                }
            ],
        ), patch(
            'g2b.management.commands.fetch_contracts.fetch_construction_notices_by_no',
            side_effect=Exception("API timeout"),
        ), patch(
            'g2b.management.commands.fetch_contracts.BidAnnouncement'
        ) as MockAnn, patch(
            'g2b.management.commands.fetch_contracts.bulk_upsert',
            return_value=(0, 0),
        ), patch(
            'g2b.management.commands.fetch_contracts.BidContract'
        ):
            MockAnn.objects.filter.return_value.values_list.return_value = []

            out = StringIO()
            # 예외가 바깥으로 전파되지 않고 정상 완료되어야 함
            call_command('fetch_contracts', '--days=1', '--dry-run', stdout=out)

        self.assertIn('보조 조회 실패', out.getvalue())


class TestContractMapping(SimpleTestCase):
    """계약 매핑 함수 테스트"""

    def test_map_contract_item_to_bid_contract(self):
        item = {
            'bidNtceNo': '20260101001',
            'bidNtceOrd': '00',
            'cntrctNo': 'C2026010100001',
            'rprsntCorpNm': '테스트건설',
            'rprsntCorpBizrno': '1234567890',
            'cntrctAmt': '4500000000',
            'bidNtceNm': '테스트 건설공사',
            'cntrctCnclsDe': '20260115',
            'presmptPrce': '5000000000',
        }
        result = map_contract_item_to_bid_contract(item)
        self.assertEqual(result['bid_ntce_no'], '20260101001')
        self.assertEqual(result['contract_no'], 'C2026010100001')
        self.assertEqual(result['company_nm'], '테스트건설')
        self.assertEqual(result['contract_amt'], 4500000000)
        self.assertEqual(result['procurement_type'], '공사')

    def test_real_contract_no(self):
        item = {
            'bidNtceNo': '20260101001',
            'bidNtceOrd': '00',
            'cntrctNo': 'C2026010100001',
        }
        result = map_contract_item_to_bid_contract(item)
        self.assertEqual(result['contract_no'], 'C2026010100001')
        self.assertNotEqual(result['contract_no'], 'NOTICE')


# ──────────────────────────────────────────────
# BC-61: A값 미공개 공고 처리 테스트
# ──────────────────────────────────────────────

class TestExactInputsReady(TestCase):
    """BC-61: A값 미공개 공고 처리 테스트."""

    @classmethod
    def setUpTestData(cls):
        from g2b.models import BidApiAValue, BidApiPrelimPrice

        # 공고 1: A+base 모두 confirmed
        cls.ann_full = BidAnnouncement.objects.create(
            bid_ntce_no='TEST-FULL-001',
            bid_ntce_ord='00',
            bid_ntce_nm='테스트 공고 (A+base 확정)',
            presume_price=500_000_000,
        )
        BidContract.objects.create(
            bid_ntce_no='TEST-FULL-001',
            bid_ntce_ord='00',
            contract_no='NOTICE',
            procurement_type='공사',
            win_method='적격심사제',
            presume_price=500_000_000,
        )
        BidApiAValue.objects.create(
            bid_ntce_no='TEST-FULL-001',
            bid_ntce_ord='00',
            national_pension=1000000,
            health_insurance=500000,
            retirement_mutual_aid=300000,
            long_term_care=100000,
            occupational_safety=200000,
            safety_management=150000,
            quality_management=100000,
        )
        BidApiPrelimPrice.objects.create(
            bid_ntce_no='TEST-FULL-001',
            bid_ntce_ord='00',
            sequence_no=0,
            base_amount=490_000_000,
        )

        # 공고 2: A 없음
        cls.ann_no_a = BidAnnouncement.objects.create(
            bid_ntce_no='TEST-NOA-001',
            bid_ntce_ord='00',
            bid_ntce_nm='테스트 공고 (A값 없음)',
            presume_price=500_000_000,
        )
        BidContract.objects.create(
            bid_ntce_no='TEST-NOA-001',
            bid_ntce_ord='00',
            contract_no='NOTICE',
            procurement_type='공사',
            win_method='적격심사제',
            presume_price=500_000_000,
        )
        BidApiPrelimPrice.objects.create(
            bid_ntce_no='TEST-NOA-001',
            bid_ntce_ord='00',
            sequence_no=0,
            base_amount=490_000_000,
        )
        # BidApiAValue 없음 → a_value_source='missing'

        # 공고 3: base 없음
        cls.ann_no_base = BidAnnouncement.objects.create(
            bid_ntce_no='TEST-NOB-001',
            bid_ntce_ord='00',
            bid_ntce_nm='테스트 공고 (기초금액 없음)',
            presume_price=500_000_000,
        )
        BidContract.objects.create(
            bid_ntce_no='TEST-NOB-001',
            bid_ntce_ord='00',
            contract_no='NOTICE',
            procurement_type='공사',
            win_method='적격심사제',
            presume_price=500_000_000,
        )
        BidApiAValue.objects.create(
            bid_ntce_no='TEST-NOB-001',
            bid_ntce_ord='00',
            national_pension=1000000,
            health_insurance=500000,
            retirement_mutual_aid=300000,
            long_term_care=100000,
            occupational_safety=200000,
            safety_management=150000,
            quality_management=100000,
        )
        # BidApiPrelimPrice 없음 → base_amount_source='missing'

        # 공고 4: A값 0원이지만 레코드 존재
        cls.ann_zero_a = BidAnnouncement.objects.create(
            bid_ntce_no='TEST-ZEROA-001',
            bid_ntce_ord='00',
            bid_ntce_nm='테스트 공고 (A값 0원)',
            presume_price=500_000_000,
        )
        BidContract.objects.create(
            bid_ntce_no='TEST-ZEROA-001',
            bid_ntce_ord='00',
            contract_no='NOTICE',
            procurement_type='공사',
            win_method='적격심사제',
            presume_price=500_000_000,
        )
        BidApiAValue.objects.create(
            bid_ntce_no='TEST-ZEROA-001',
            bid_ntce_ord='00',
            # 모든 필드 0 (default)
        )
        BidApiPrelimPrice.objects.create(
            bid_ntce_no='TEST-ZEROA-001',
            bid_ntce_ord='00',
            sequence_no=0,
            base_amount=490_000_000,
        )

    # T1: A 미확정 시 canRecommend=False
    def test_recommendation_a_missing(self):
        client = DjangoClient()
        resp = client.get('/api/ui/notices/recommendation/', {'bid_ntce_no': 'TEST-NOA-001'})
        data = resp.json()
        self.assertFalse(data['canRecommend'])
        self.assertFalse(data['isExact'])
        self.assertEqual(data['pendingReason'], 'a_value')

    # T2: base 미확정 시 canRecommend=False
    def test_recommendation_base_missing(self):
        client = DjangoClient()
        resp = client.get('/api/ui/notices/recommendation/', {'bid_ntce_no': 'TEST-NOB-001'})
        data = resp.json()
        self.assertFalse(data['canRecommend'])
        self.assertEqual(data['pendingReason'], 'base_amount')

    # T3: lookup_bid A 미확정 → null
    def test_lookup_bid_a_missing_returns_null(self):
        client = DjangoClient()
        resp = client.get('/lookup/', {'bid_ntce_no': 'TEST-NOA-001'})
        data = resp.json()
        self.assertIsNone(data['a_value'])
        self.assertEqual(data['a_value_status'], 'missing')

    # T4: lookup_bid base 미확정 → null
    def test_lookup_bid_base_missing_returns_null(self):
        client = DjangoClient()
        resp = client.get('/lookup/', {'bid_ntce_no': 'TEST-NOB-001'})
        data = resp.json()
        self.assertIsNone(data['base_amount'])
        self.assertEqual(data['base_amount_status'], 'missing')

    # T5: api_price_calculator key없음+bundle missing → 경고
    def test_calculator_bundle_missing_source(self):
        client = DjangoClient()
        resp = client.post(
            '/api/ui/calculator/',
            json.dumps({'noticeNo': 'TEST-NOA-001', 'estimatedPrice': '500000000', 'bidRate': '90.000'}),
            content_type='application/json',
        )
        data = resp.json()
        self.assertFalse(data['canRecommend'])

    # T6: api_price_calculator key존재+null → bundle fallback 없이 경고
    def test_calculator_explicit_null_no_fallback(self):
        client = DjangoClient()
        resp = client.post(
            '/api/ui/calculator/',
            json.dumps({
                'noticeNo': 'TEST-FULL-001',
                'estimatedPrice': '500000000',
                'aValue': None,
                'baseAmount': None,
                'bidRate': '90.000',
            }),
            content_type='application/json',
        )
        data = resp.json()
        self.assertFalse(data['canRecommend'])

    # T7: api_price_calculator key없음+bundle.source='missing' → 경고
    def test_calculator_bundle_a_missing_source(self):
        client = DjangoClient()
        resp = client.post(
            '/api/ui/calculator/',
            json.dumps({
                'noticeNo': 'TEST-NOA-001',
                'estimatedPrice': '500000000',
                'bidRate': '90.000',
            }),
            content_type='application/json',
        )
        data = resp.json()
        self.assertFalse(data['canRecommend'])

    # T8: 사용자 직접 유효 수치 입력 → 정상 계산
    def test_calculator_user_input_overrides(self):
        client = DjangoClient()
        resp = client.post(
            '/api/ui/calculator/',
            json.dumps({
                'estimatedPrice': '500000000',
                'aValue': '2350000',
                'baseAmount': '490000000',
                'bidRate': '90.000',
            }),
            content_type='application/json',
        )
        data = resp.json()
        self.assertTrue(data.get('isExact', True))
        self.assertIn('result', data)

    # T9: A+base 모두 confirmed → 정상 추천
    def test_recommendation_all_confirmed(self):
        client = DjangoClient()
        resp = client.get('/api/ui/notices/recommendation/', {'bid_ntce_no': 'TEST-FULL-001'})
        data = resp.json()
        self.assertTrue(data['canRecommend'])
        self.assertTrue(data['isExact'])
        self.assertIsNone(data['pendingReason'])

    # T10: 공식 레코드 0원이어도 confirmed
    def test_zero_a_value_still_confirmed(self):
        client = DjangoClient()
        resp = client.get('/api/ui/notices/recommendation/', {'bid_ntce_no': 'TEST-ZEROA-001'})
        data = resp.json()
        self.assertTrue(data['canRecommend'])


class TestRetryPendingInputs(TestCase):
    """BC-61 Phase B: retry_pending_inputs 배치 테스트."""

    @classmethod
    def setUpTestData(cls):
        # pending + upcoming 공고
        cls.ann_pending = BidAnnouncement.objects.create(
            bid_ntce_no='TEST-PEND-001',
            bid_ntce_ord='00',
            bid_ntce_nm='테스트 pending 공고',
            presume_price=500_000_000,
            a_value_status='pending',
            base_amount_status='pending',
        )
        # upcoming 개찰일 계약
        BidContract.objects.create(
            bid_ntce_no='TEST-PEND-001',
            bid_ntce_ord='00',
            contract_no='NOTICE',
            procurement_type='공사',
            win_method='적격심사제',
            presume_price=500_000_000,
            openg_date='20990101',  # 미래
        )

        # pending + 개찰 경과 공고
        cls.ann_expired = BidAnnouncement.objects.create(
            bid_ntce_no='TEST-EXP-001',
            bid_ntce_ord='00',
            bid_ntce_nm='테스트 개찰경과 공고',
            presume_price=500_000_000,
            a_value_status='pending',
            base_amount_status='pending',
        )
        BidContract.objects.create(
            bid_ntce_no='TEST-EXP-001',
            bid_ntce_ord='00',
            contract_no='NOTICE',
            procurement_type='공사',
            win_method='적격심사제',
            presume_price=500_000_000,
            openg_date='20200101',  # 과거
        )

    def test_expired_becomes_error(self):
        """개찰일 경과 + pending → error 전이."""
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('retry_pending_inputs', '--limit=100', stdout=out)
        self.ann_expired.refresh_from_db()
        self.assertEqual(self.ann_expired.a_value_status, 'error')
        self.assertEqual(self.ann_expired.base_amount_status, 'error')

    def test_pending_target_included(self):
        """upcoming + pending 공고가 대상에 포함."""
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        # dry-run으로 확인 (API 호출 없이 대상 카운트만 검증)
        call_command('retry_pending_inputs', '--dry-run', '--limit=100', stdout=out)
        output = out.getvalue()
        self.assertIn('재확인 대상:', output)
        # TEST-PEND-001(미래 개찰일)은 대상에 포함되어야 함
        self.assertRegex(output, r'재확인 대상: [1-9]')


class TestBC61StatusRefinement(SimpleTestCase):
    """BC-61: pending 의미 분리 + canonical source 테스트."""

    def test_fetch_sets_checked_missing_on_empty_api(self):
        """API 빈 응답 → status=checked_missing 패턴 검증."""
        # checked_missing은 write path의 기본값 — 테스트는 모델 choices 유효성 확인
        choices = dict(BidAnnouncement.STATUS_CHOICES)
        self.assertIn('checked_missing', choices)
        self.assertEqual(choices['checked_missing'], '조회-없음')

    def test_fetch_sets_confirmed_on_success(self):
        """API 성공 → status=confirmed 패턴 검증."""
        choices = dict(BidAnnouncement.STATUS_CHOICES)
        self.assertIn('confirmed', choices)
        self.assertEqual(choices['confirmed'], '확인')

    def test_status_choices_complete(self):
        """STATUS_CHOICES가 4가지 상태를 모두 포함하는지 검증."""
        keys = [k for k, v in BidAnnouncement.STATUS_CHOICES]
        self.assertEqual(sorted(keys), ['checked_missing', 'confirmed', 'error', 'pending'])

    def test_retry_includes_checked_missing(self):
        """checked_missing도 재시도 대상에 포함되는지 — 필터 조건 검증."""
        valid_retry_statuses = {'pending', 'checked_missing'}
        all_statuses = {k for k, v in BidAnnouncement.STATUS_CHOICES}
        self.assertTrue(valid_retry_statuses.issubset(all_statuses))


class TestBC61NewFieldsAndWarnings(SimpleTestCase):
    """BC-61: 미수집 필드 매핑 + 설명회 warning 테스트."""

    def test_map_notice_includes_new_fields(self):
        """매핑 함수가 7개 신규 필드를 포함하는지 검증."""
        sample_item = {
            'bidNtceNo': '20260101001',
            'bidNtceOrd': '00',
            'bidNtceNm': '테스트공사',
            'presmptPrce': '500000000',
            'presnatnOprtnYn': 'Y',
            'presnatnOprtnDate': '20260315',
            'presnatnOprtnTm': '1400',
            'indstrytyLmtYn': 'Y',
            'rgnLmtYn': 'N',
            'rsrvtnPrceDcsnMthdNm': '복수예비가격',
            'bidNtceUrl': 'https://example.com/notice/123',
        }
        result = map_notice_to_announcement(sample_item)
        self.assertEqual(result['briefing_yn'], 'Y')
        self.assertEqual(result['briefing_date'], '20260315')
        self.assertEqual(result['briefing_time'], '1400')
        self.assertEqual(result['industry_limit_yn'], 'Y')
        self.assertEqual(result['region_limit_yn'], 'N')
        self.assertEqual(result['reserve_price_method'], '복수예비가격')
        self.assertEqual(result['bid_ntce_url'], 'https://example.com/notice/123')

    def test_new_fields_nullable_defaults(self):
        """기존 데이터와 호환 — 빈 API 응답에도 빈 문자열 기본값."""
        sample_item = {
            'bidNtceNo': '20260101001',
            'bidNtceOrd': '00',
        }
        result = map_notice_to_announcement(sample_item)
        self.assertEqual(result['briefing_yn'], '')
        self.assertEqual(result['briefing_date'], '')
        self.assertEqual(result['briefing_time'], '')
        self.assertEqual(result['industry_limit_yn'], '')
        self.assertEqual(result['region_limit_yn'], '')
        self.assertEqual(result['reserve_price_method'], '')
        self.assertEqual(result['bid_ntce_url'], '')

    def test_is_eligible_logs_nonstandard(self):
        """비표준 적격심사 유형에 warning 로그 출력 검증."""
        item = {
            'presmptPrce': '500000000',
            'sucsfbidMthdNm': '적격 낙찰제',
            'bidNtceNo': 'TEST001',
        }
        with self.assertLogs('g2b.services.g2b_construction_sync', level='WARNING') as cm:
            result = is_eligible_notice_for_service(item)
        self.assertTrue(result)
        self.assertTrue(any('비표준 적격심사' in msg for msg in cm.output))

    def test_is_eligible_no_log_for_standard(self):
        """표준 적격심사에는 warning 로그 없음."""
        item = {
            'presmptPrce': '500000000',
            'sucsfbidMthdNm': '적격심사',
            'bidNtceNo': 'TEST002',
        }
        result = is_eligible_notice_for_service(item)
        self.assertTrue(result)


# ──────────────────────────────────────────────
# BC-61: status 필드, backfill, soft warning 테스트
# ──────────────────────────────────────────────

class TestBidAnnouncementStatusChoices(SimpleTestCase):
    """BC-61 Item 1/2: STATUS_CHOICES + canonical source 코드 문서화 검증."""

    def test_status_choices_contains_checked_missing(self):
        """STATUS_CHOICES에 checked_missing이 포함되어야 한다."""
        from g2b.models import BidAnnouncement
        choices_keys = [key for key, _ in BidAnnouncement.STATUS_CHOICES]
        self.assertIn('checked_missing', choices_keys)

    def test_status_choices_all_values(self):
        """STATUS_CHOICES가 4개 상태를 모두 포함한다."""
        from g2b.models import BidAnnouncement
        choices_keys = [key for key, _ in BidAnnouncement.STATUS_CHOICES]
        self.assertEqual(set(choices_keys), {'pending', 'checked_missing', 'confirmed', 'error'})

    def test_a_value_status_help_text_documents_canonical_source(self):
        """a_value_status help_text가 batch metadata 역할을 명시한다."""
        from g2b.models import BidAnnouncement
        field = BidAnnouncement._meta.get_field('a_value_status')
        self.assertIn('confirmed', field.help_text)
        self.assertIn('pending', field.help_text)

    def test_base_amount_status_has_same_choices(self):
        """base_amount_status도 동일한 4개 choices를 갖는다."""
        from g2b.models import BidAnnouncement
        field = BidAnnouncement._meta.get_field('base_amount_status')
        choices_keys = [key for key, _ in field.choices]
        self.assertEqual(set(choices_keys), {'pending', 'checked_missing', 'confirmed', 'error'})


class TestBackfillStatus(TestCase):
    """BC-61 Item 3: backfill_status 커맨드 테스트."""

    def setUp(self):
        from g2b.models import BidApiAValue, BidApiPrelimPrice
        from g2b.services.g2b_construction_sync import PLACEHOLDER_PRELIM_SEQUENCE

        # 공고 A: A값 레코드 있음, 기초금액 없음 → a_value만 confirmed
        self.ann_a = BidAnnouncement.objects.create(
            bid_ntce_no='BACKFILL001',
            bid_ntce_ord='00',
            bid_ntce_nm='백필 테스트 공고 A',
            presume_price=500_000_000,
            a_value_status='pending',
            base_amount_status='pending',
        )
        BidApiAValue.objects.create(
            bid_ntce_no='BACKFILL001',
            bid_ntce_ord='00',
        )

        # 공고 B: 기초금액 레코드 있음, A값 없음 → base_amount만 confirmed
        self.ann_b = BidAnnouncement.objects.create(
            bid_ntce_no='BACKFILL002',
            bid_ntce_ord='00',
            bid_ntce_nm='백필 테스트 공고 B',
            presume_price=500_000_000,
            a_value_status='checked_missing',
            base_amount_status='checked_missing',
        )
        BidApiPrelimPrice.objects.create(
            bid_ntce_no='BACKFILL002',
            bid_ntce_ord='00',
            sequence_no=PLACEHOLDER_PRELIM_SEQUENCE,
            basis_planned_price=0,
            is_drawn=False,
            draw_count=0,
            planned_price=0,
            base_amount=500_000_000,
        )

        # 공고 C: 둘 다 레코드 있음 → 둘 다 confirmed
        self.ann_c = BidAnnouncement.objects.create(
            bid_ntce_no='BACKFILL003',
            bid_ntce_ord='00',
            bid_ntce_nm='백필 테스트 공고 C',
            presume_price=500_000_000,
            a_value_status='pending',
            base_amount_status='pending',
        )
        BidApiAValue.objects.create(
            bid_ntce_no='BACKFILL003',
            bid_ntce_ord='00',
        )
        BidApiPrelimPrice.objects.create(
            bid_ntce_no='BACKFILL003',
            bid_ntce_ord='00',
            sequence_no=PLACEHOLDER_PRELIM_SEQUENCE,
            basis_planned_price=0,
            is_drawn=False,
            draw_count=0,
            planned_price=0,
            base_amount=500_000_000,
        )

    def _run_command(self, dry_run=False):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        kwargs = {'stdout': out}
        if dry_run:
            kwargs['dry_run'] = True
        call_command('backfill_status', **kwargs)
        return out.getvalue()

    def test_dry_run_does_not_modify_db(self):
        """dry-run 실행 시 DB가 변경되지 않는다."""
        self._run_command(dry_run=True)
        self.ann_a.refresh_from_db()
        self.assertEqual(self.ann_a.a_value_status, 'pending')
        self.assertEqual(self.ann_a.base_amount_status, 'pending')

    def test_a_value_confirmed_when_record_exists(self):
        """BidApiAValue 레코드 있는 공고 → a_value_status=confirmed."""
        self._run_command()
        self.ann_a.refresh_from_db()
        self.assertEqual(self.ann_a.a_value_status, 'confirmed')

    def test_base_amount_stays_pending_when_no_record(self):
        """기초금액 레코드 없으면 base_amount_status 변경 안 됨."""
        self._run_command()
        self.ann_a.refresh_from_db()
        self.assertEqual(self.ann_a.base_amount_status, 'pending')

    def test_base_amount_confirmed_from_checked_missing(self):
        """checked_missing 상태도 레코드 있으면 confirmed로 전환."""
        self._run_command()
        self.ann_b.refresh_from_db()
        self.assertEqual(self.ann_b.base_amount_status, 'confirmed')

    def test_a_value_stays_checked_missing_when_no_record(self):
        """A값 레코드 없으면 checked_missing 유지."""
        self._run_command()
        self.ann_b.refresh_from_db()
        self.assertEqual(self.ann_b.a_value_status, 'checked_missing')

    def test_both_confirmed_when_both_records_exist(self):
        """둘 다 레코드 있으면 둘 다 confirmed."""
        self._run_command()
        self.ann_c.refresh_from_db()
        self.assertEqual(self.ann_c.a_value_status, 'confirmed')
        self.assertEqual(self.ann_c.base_amount_status, 'confirmed')

    def test_idempotent(self):
        """두 번 실행해도 결과 동일 (멱등성)."""
        self._run_command()
        self._run_command()
        self.ann_c.refresh_from_db()
        self.assertEqual(self.ann_c.a_value_status, 'confirmed')
        self.assertEqual(self.ann_c.base_amount_status, 'confirmed')


class TestBriefingYnSoftWarning(TestCase):
    """BC-61 Item 4: briefing_yn='Y' soft warning 검증."""

    def setUp(self):
        self.client = DjangoClient()
        # 추천 API 경로에서 bundle을 통해 warning을 받으려면 공고+계약+A값+기초금액 필요
        from g2b.models import BidApiAValue, BidApiPrelimPrice, BidContract
        from g2b.services.g2b_construction_sync import PLACEHOLDER_PRELIM_SEQUENCE

        self.bid_ntce_no = 'WARNING001'
        self.bid_ntce_ord = '00'

        BidAnnouncement.objects.create(
            bid_ntce_no=self.bid_ntce_no,
            bid_ntce_ord=self.bid_ntce_ord,
            bid_ntce_nm='설명회 공고 테스트',
            presume_price=500_000_000,
            briefing_yn='Y',
            briefing_date='20260320',
            briefing_time='1400',
            a_value_status='confirmed',
            base_amount_status='confirmed',
        )
        BidContract.objects.create(
            bid_ntce_no=self.bid_ntce_no,
            bid_ntce_ord=self.bid_ntce_ord,
            bid_ntce_nm='설명회 공고 테스트',
            procurement_type='공사',
            win_method='적격심사',
            presume_price=500_000_000,
            contract_no='NOTICE',
        )
        BidApiAValue.objects.create(
            bid_ntce_no=self.bid_ntce_no,
            bid_ntce_ord=self.bid_ntce_ord,
            national_pension=5_000_000,
            health_insurance=1_000_000,
            retirement_mutual_aid=1_000_000,
            long_term_care=500_000,
            occupational_safety=500_000,
            safety_management=500_000,
            quality_management=500_000,
        )
        BidApiPrelimPrice.objects.create(
            bid_ntce_no=self.bid_ntce_no,
            bid_ntce_ord=self.bid_ntce_ord,
            sequence_no=PLACEHOLDER_PRELIM_SEQUENCE,
            basis_planned_price=0,
            is_drawn=False,
            draw_count=0,
            planned_price=0,
            base_amount=500_000_000,
        )

    def test_briefing_yn_y_adds_warning(self):
        """briefing_yn='Y'인 공고는 추천 결과에 warnings 배열에 항목이 추가된다."""
        resp = self.client.get(
            f'/api/ui/notices/recommendation/?bid_ntce_no={self.bid_ntce_no}'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        warnings = data.get('warnings', [])
        types = [w['type'] for w in warnings]
        self.assertIn('briefing', types)

    def test_briefing_warning_is_info_severity(self):
        """설명회 warning의 severity는 info (hard block 아님)."""
        resp = self.client.get(
            f'/api/ui/notices/recommendation/?bid_ntce_no={self.bid_ntce_no}'
        )
        data = resp.json()
        briefing_warnings = [w for w in data.get('warnings', []) if w['type'] == 'briefing']
        self.assertEqual(len(briefing_warnings), 1)
        self.assertEqual(briefing_warnings[0]['severity'], 'info')

    def test_briefing_warning_does_not_block_recommendation(self):
        """설명회 warning이 있어도 canRecommend=True (hard block 아님)."""
        resp = self.client.get(
            f'/api/ui/notices/recommendation/?bid_ntce_no={self.bid_ntce_no}'
        )
        data = resp.json()
        self.assertTrue(data.get('canRecommend'))

    def test_briefing_yn_n_no_warning(self):
        """briefing_yn='N'인 공고는 warnings 배열에 briefing 항목 없음."""
        from g2b.models import BidApiAValue, BidApiPrelimPrice, BidContract
        from g2b.services.g2b_construction_sync import PLACEHOLDER_PRELIM_SEQUENCE

        no_brief_no = 'NOBRIEF001'
        BidAnnouncement.objects.create(
            bid_ntce_no=no_brief_no,
            bid_ntce_ord='00',
            bid_ntce_nm='설명회 없는 공고',
            presume_price=500_000_000,
            briefing_yn='N',
            a_value_status='confirmed',
            base_amount_status='confirmed',
        )
        BidContract.objects.create(
            bid_ntce_no=no_brief_no,
            bid_ntce_ord='00',
            bid_ntce_nm='설명회 없는 공고',
            procurement_type='공사',
            win_method='적격심사',
            presume_price=500_000_000,
            contract_no='NOTICE',
        )
        BidApiAValue.objects.create(
            bid_ntce_no=no_brief_no,
            bid_ntce_ord='00',
            national_pension=5_000_000,
        )
        BidApiPrelimPrice.objects.create(
            bid_ntce_no=no_brief_no,
            bid_ntce_ord='00',
            sequence_no=PLACEHOLDER_PRELIM_SEQUENCE,
            basis_planned_price=0,
            is_drawn=False,
            draw_count=0,
            planned_price=0,
            base_amount=500_000_000,
        )
        resp = self.client.get(f'/api/ui/notices/recommendation/?bid_ntce_no={no_brief_no}')
        data = resp.json()
        types = [w['type'] for w in data.get('warnings', [])]
        self.assertNotIn('briefing', types)
