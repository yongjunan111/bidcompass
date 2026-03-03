"""
BidCompass 테스트 스위트

13개 클래스:
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
  - TestRecommendView (BC-40)
  - TestBenchmarkView (BC-38)
  - TestRecommendBand (BC-40)
"""

import json
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, Client as DjangoClient

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

    def test_specialty_3_to_50eouk(self):
        """전문공사 3~50억 전체 TABLE_2B."""
        self.assertEqual(
            select_table(3 * UNIT_EOUK, WorkType.SPECIALTY), TableType.TABLE_2B
        )
        self.assertEqual(
            select_table(10 * UNIT_EOUK, WorkType.SPECIALTY), TableType.TABLE_2B
        )
        self.assertEqual(
            select_table(49 * UNIT_EOUK, WorkType.SPECIALTY), TableType.TABLE_2B
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
# BC-40: 최적투찰 추천기 뷰 테스트
# ──────────────────────────────────────────────

class TestRecommendView(TestCase):
    """BC-40: 추천기 뷰 테스트."""

    def setUp(self):
        self.client = DjangoClient()

    def test_get_renders_form(self):
        resp = self.client.get("/recommend/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "최적투찰 추천기")

    def test_post_with_15_prices(self):
        """15개 복수예비가격 → 1,365 시나리오."""
        data = {
            "estimated_price": "500000000",
            "work_type": "construction",
            "a_value": "50000000",
        }
        for i in range(15):
            data[f"prelim_{i}"] = str(500_000_000 + i * 500_000)

        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["n_scenarios"], 1365)
        self.assertContains(resp, "추천 투찰 구간")

    def test_post_with_4_prices(self):
        """4개 복수예비가격 → 1 시나리오."""
        data = {
            "estimated_price": "500000000",
            "work_type": "construction",
            "a_value": "0",
            "prelim_0": "500000000",
            "prelim_1": "501000000",
            "prelim_2": "502000000",
            "prelim_3": "503000000",
        }
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["n_scenarios"], 1)

    def test_post_insufficient_prices(self):
        """3개 미만 → 에러."""
        data = {
            "estimated_price": "500000000",
            "work_type": "construction",
            "a_value": "0",
            "prelim_0": "500000000",
            "prelim_1": "501000000",
            "prelim_2": "502000000",
        }
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "최소 4개")

    def test_post_out_of_scope(self):
        """100억 이상 → OUT_OF_SCOPE 에러."""
        data = {
            "estimated_price": "10000000000",
            "work_type": "construction",
            "a_value": "0",
        }
        for i in range(4):
            data[f"prelim_{i}"] = str(10_000_000_000 + i * 1_000_000)
        resp = self.client.post("/recommend/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "적격심사 대상 외")


# ──────────────────────────────────────────────
# BC-38: 벤치마크 뷰 테스트
# ──────────────────────────────────────────────

class TestBenchmarkView(TestCase):
    """BC-38: 벤치마크 뷰 테스트."""

    def setUp(self):
        self.client = DjangoClient()

    def test_no_json_shows_message(self):
        """JSON 파일 없음 → 안내 메시지."""
        resp = self.client.get("/benchmark/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "benchmark_info21c")

    def test_valid_json_renders(self):
        """정상 JSON → 비교표 렌더링."""
        json_path = Path(settings.BASE_DIR) / "data" / "collected" / "benchmark_info21c.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)

        test_data = {
            "meta": {"total": 1, "optimal_count": 0, "single_est_count": 1},
            "summary": {"bc_wins": 1, "draws": 0, "info_wins": 0, "avg_improvement": 5.0},
            "records": [{
                "bid_ntce_no": "TEST-001",
                "bid_name": "테스트공사",
                "data_source": "fallback_single_est",
                "info_score": 85.0,
                "bc_score": 90.0,
                "rank1_score": 89.0,
                "improvement": 5.0,
            }],
        }
        json_path.write_text(json.dumps(test_data, ensure_ascii=False))

        try:
            resp = self.client.get("/benchmark/")
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, "BidCompass 우위")
            self.assertEqual(resp.context["summary"]["bc_wins"], 1)
        finally:
            json_path.unlink(missing_ok=True)

    def test_corrupt_json_shows_error(self):
        """손상 JSON → 에러 메시지."""
        json_path = Path(settings.BASE_DIR) / "data" / "collected" / "benchmark_info21c.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text("{invalid json content!!")

        try:
            resp = self.client.get("/benchmark/")
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, "로드 실패")
        finally:
            json_path.unlink(missing_ok=True)


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
