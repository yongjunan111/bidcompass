"""
BidCompass 코어엔진 테스트 스위트

7개 클래스, SimpleTestCase (DB 불필요):
  - TestRoundingHelpers
  - TestSelectTable
  - TestCalculateAValue
  - TestCheckNetCostExclusion
  - TestCalcPriceScore
  - TestGetFloorRate
  - TestBidAnalysisEngine
"""

from decimal import Decimal

from django.test import SimpleTestCase

from g2b.services.bid_engine import (
    AValueItems,
    BidAnalysisEngine,
    ExclusionStatus,
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
