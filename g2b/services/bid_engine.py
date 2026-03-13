"""
BidCompass 코어엔진 — 적격심사 가격점수 분석

모듈:
  - select_table (BC-22): 추정가격/공사구분 → 별표 라우팅
  - calculate_a_value (BC-25): A값 7개 항목 합산
  - check_net_cost_exclusion (BC-24): 순공사원가 98% 배제 판정
  - calc_price_score (BC-23): 가격점수 계산
  - BidAnalysisEngine (BC-26): 통합 파이프라인

조달청지침 #9269 (시행 2025.12.1 / 입찰가격평가 2026.1.30) 기반.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_DOWN, ROUND_HALF_UP, Decimal
from enum import Enum
from typing import List, Optional


# ──────────────────────────────────────────────
# 반올림 헬퍼 3종 — round() 금지, Decimal 전용
# ──────────────────────────────────────────────

def round_half_up(value: Decimal, places: int) -> Decimal:
    """소수점 places 자리로 사사오입 반올림."""
    if not isinstance(value, Decimal):
        raise TypeError(f"Decimal required, got {type(value).__name__}")
    quantize_str = Decimal(10) ** -places
    return value.quantize(quantize_str, rounding=ROUND_HALF_UP)


def truncate(value: Decimal, places: int) -> Decimal:
    """소수점 places 자리 아래 절사."""
    if not isinstance(value, Decimal):
        raise TypeError(f"Decimal required, got {type(value).__name__}")
    quantize_str = Decimal(10) ** -places
    return value.quantize(quantize_str, rounding=ROUND_DOWN)


def ceil_up(value: int | Decimal) -> int:
    """1원 미만 올림 (정수 반환)."""
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return int(value.to_integral_value(rounding=ROUND_CEILING))
    raise TypeError(f"int or Decimal required, got {type(value).__name__}")


# ──────────────────────────────────────────────
# Enum 정의
# ──────────────────────────────────────────────

class TableType(Enum):
    TABLE_1 = "TABLE_1"
    TABLE_2A = "TABLE_2A"
    TABLE_2B = "TABLE_2B"
    TABLE_3 = "TABLE_3"
    TABLE_4 = "TABLE_4"
    TABLE_5 = "TABLE_5"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class WorkType(Enum):
    CONSTRUCTION = "construction"
    SPECIALTY = "specialty"  # 전기/정보통신/소방/국가유산


class ExclusionStatus(Enum):
    EXCLUDED = "excluded"
    PASSED = "passed"
    NOT_CHECKED = "not_checked"


# ──────────────────────────────────────────────
# Dataclass 정의 — 입력/출력
# ──────────────────────────────────────────────

@dataclass
class TableParams:
    max_score: Decimal
    coeff: Decimal
    fixed_ratio: Decimal
    fixed_score: Decimal


@dataclass
class AValueItems:
    national_pension: int = 0           # 국민연금보험료
    health_insurance: int = 0           # 국민건강보험료
    retirement_mutual_aid: int = 0      # 퇴직공제부금비
    long_term_care: int = 0             # 노인장기요양보험료
    occupational_safety: int = 0        # 산업안전보건관리비
    safety_management: int = 0          # 안전관리비
    quality_management: int = 0         # 품질관리비


@dataclass
class PriceScoreResult:
    score: Decimal
    ratio: Decimal
    is_fixed_score: bool
    table_type: TableType


@dataclass
class NetCostExclusionResult:
    status: ExclusionStatus
    threshold: int
    message: str


@dataclass
class ScoreHeatmapPoint:
    bid_rate: Decimal       # 투찰률 (예: 0.8975)
    bid_amount: int         # 투찰금액 (원)
    price_score: Decimal    # 가격점수
    is_fixed_score: bool


@dataclass
class BidAnalysisResult:
    table_type: TableType
    a_value: int
    is_out_of_scope: bool = False

    # 배제 판정
    exclusion_result: Optional[NetCostExclusionResult] = None

    # 가격점수 — 배제 시 reference_price_score로 저장
    price_score_result: Optional[PriceScoreResult] = None
    reference_price_score: Optional[Decimal] = None

    # 최종 판정
    final_pass: bool = True

    # 히트맵
    score_heatmap: List[ScoreHeatmapPoint] = field(default_factory=list)

    # 메시지
    messages: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# 상수/설정 테이블
# ──────────────────────────────────────────────

UNIT_EOUK = 1_0000_0000  # 1억원

TABLE_PARAMS_MAP: dict[TableType, TableParams] = {
    TableType.TABLE_1: TableParams(
        max_score=Decimal("50"), coeff=Decimal("2"),
        fixed_ratio=Decimal("0.925"), fixed_score=Decimal("45"),
    ),
    TableType.TABLE_2A: TableParams(
        max_score=Decimal("70"), coeff=Decimal("4"),
        fixed_ratio=Decimal("0.9125"), fixed_score=Decimal("65"),
    ),
    TableType.TABLE_2B: TableParams(
        max_score=Decimal("70"), coeff=Decimal("20"),
        fixed_ratio=Decimal("0.9025"), fixed_score=Decimal("65"),
    ),
    TableType.TABLE_3: TableParams(
        max_score=Decimal("80"), coeff=Decimal("20"),
        fixed_ratio=Decimal("0.9025"), fixed_score=Decimal("75"),
    ),
    TableType.TABLE_4: TableParams(
        max_score=Decimal("90"), coeff=Decimal("20"),
        fixed_ratio=Decimal("0.9025"), fixed_score=Decimal("85"),
    ),
    TableType.TABLE_5: TableParams(
        max_score=Decimal("90"), coeff=Decimal("20"),
        fixed_ratio=Decimal("0.9025"), fixed_score=Decimal("85"),
    ),
}

BASE_RATE = Decimal("90")
MIN_SCORE = Decimal("2")

# 낙찰하한율 (2026.1.30 시행, +2%p 상향)
# 경계: [하한, 상한) — ≥100억 방어적 포함
FLOOR_RATE_TABLE: list[tuple[int, int, Decimal]] = [
    (0,              10 * UNIT_EOUK,   Decimal("89.745")),
    (10 * UNIT_EOUK, 50 * UNIT_EOUK,   Decimal("88.745")),
    (50 * UNIT_EOUK, 100 * UNIT_EOUK,  Decimal("87.495")),
    (100 * UNIT_EOUK, 300 * UNIT_EOUK, Decimal("81.995")),
]


def get_floor_rate(estimated_price: int) -> Decimal:
    """추정가격 구간별 낙찰하한율 반환 (방어적: ≥100억도 포함)."""
    if estimated_price <= 0:
        raise ValueError("estimated_price must be positive")
    for lower, upper, rate in FLOOR_RATE_TABLE:
        if lower <= estimated_price < upper:
            return rate
    # 300억 이상: 가장 높은 구간 반환 (방어적)
    return FLOOR_RATE_TABLE[-1][2]


# ──────────────────────────────────────────────
# BC-22: select_table — 별표 라우팅
# ──────────────────────────────────────────────

def select_table(estimated_price: int, work_type: WorkType) -> TableType:
    """추정가격(원)과 공사구분으로 적격심사 별표 결정.

    경계: [하한, 상한) 통일, 정수 비교.
    ≥100억 → OUT_OF_SCOPE (적격심사 대상 아님).
    """
    if estimated_price <= 0:
        raise ValueError("estimated_price must be positive")

    # ≥100억: 적격심사 대상 외
    if estimated_price >= 100 * UNIT_EOUK:
        return TableType.OUT_OF_SCOPE

    # 50~100억: 공사구분 무관 별표1
    if estimated_price >= 50 * UNIT_EOUK:
        return TableType.TABLE_1

    if work_type == WorkType.CONSTRUCTION:
        if estimated_price >= 10 * UNIT_EOUK:
            return TableType.TABLE_2A
        if estimated_price >= 3 * UNIT_EOUK:
            return TableType.TABLE_3
        if estimated_price >= 2 * UNIT_EOUK:
            return TableType.TABLE_4
        return TableType.TABLE_5
    else:  # SPECIALTY
        if estimated_price >= 10 * UNIT_EOUK:
            return TableType.TABLE_2A  # 10억 이상은 특수업종도 별표2-가
        if estimated_price >= 3 * UNIT_EOUK:
            return TableType.TABLE_2B  # 3~10억 특수업종만 별표2-나
        if estimated_price >= int(Decimal("0.8") * UNIT_EOUK):  # 8000만원
            return TableType.TABLE_4
        return TableType.TABLE_5


# ──────────────────────────────────────────────
# BC-25: calculate_a_value — A값 합산
# ──────────────────────────────────────────────

_A_VALUE_FIELDS = [
    "national_pension",
    "health_insurance",
    "retirement_mutual_aid",
    "long_term_care",
    "occupational_safety",
    "safety_management",
    "quality_management",
]


def calculate_a_value(items: AValueItems) -> int:
    """A값 7개 항목 합산. 음수 항목 시 ValueError."""
    total = 0
    for field_name in _A_VALUE_FIELDS:
        value = getattr(items, field_name)
        if value < 0:
            raise ValueError(f"A값 항목 '{field_name}'이(가) 음수입니다: {value}")
        total += value
    return total


# ──────────────────────────────────────────────
# BC-24: check_net_cost_exclusion — 순공사원가 배제
# ──────────────────────────────────────────────

def check_net_cost_exclusion(
    net_construction_cost: int,
    bid_amount: int,
) -> NetCostExclusionResult:
    """순공사원가의 98% 미만이면 심사대상 배제.

    threshold = ceil(순공사원가 * 98 / 100)
    bid < threshold → EXCLUDED
    """
    if net_construction_cost < 0:
        raise ValueError("net_construction_cost must be non-negative")
    if bid_amount < 0:
        raise ValueError("bid_amount must be non-negative")

    threshold = ceil_up(
        Decimal(str(net_construction_cost)) * Decimal("98") / Decimal("100")
    )

    if bid_amount < threshold:
        return NetCostExclusionResult(
            status=ExclusionStatus.EXCLUDED,
            threshold=threshold,
            message="순공사원가 98% 미달로 심사대상 제외",
        )

    return NetCostExclusionResult(
        status=ExclusionStatus.PASSED,
        threshold=threshold,
        message="순공사원가 98% 이상 — 통과",
    )


# ──────────────────────────────────────────────
# BC-23: calc_price_score — 가격점수 계산
# ──────────────────────────────────────────────

def calc_price_score(
    bid_price: int,
    estimated_price: int,
    a_value: int,
    table_type: TableType,
) -> PriceScoreResult:
    """투찰금액 기반 가격점수 계산.

    ratio = round_half_up((bid - A) / (est - A), 4)
    고정점수: bid <= est_price AND ratio >= fixed_ratio
    점수: max - coeff * |90 - ratio * 100|, 최소 2점
    """
    if estimated_price <= 0:
        raise ValueError("estimated_price must be positive")
    if bid_price < 0:
        raise ValueError("bid_price must be non-negative")
    if a_value < 0:
        raise ValueError("a_value must be non-negative")
    if a_value >= estimated_price:
        raise ValueError("a_value must be less than estimated_price")
    if table_type == TableType.OUT_OF_SCOPE:
        raise ValueError("OUT_OF_SCOPE is not a valid table for scoring")

    params = TABLE_PARAMS_MAP[table_type]

    bid_d = Decimal(str(bid_price))
    est_d = Decimal(str(estimated_price))
    a_d = Decimal(str(a_value))

    ratio = round_half_up((bid_d - a_d) / (est_d - a_d), 4)

    # 고정점수: bid <= est_price AND ratio >= fixed_ratio
    if bid_price <= estimated_price and ratio >= params.fixed_ratio:
        return PriceScoreResult(
            score=params.fixed_score,
            ratio=ratio,
            is_fixed_score=True,
            table_type=table_type,
        )

    # 일반 공식: max - coeff * |90 - ratio * 100|
    score = params.max_score - params.coeff * abs(
        BASE_RATE - ratio * Decimal("100")
    )
    score = max(score, MIN_SCORE)

    return PriceScoreResult(
        score=score,
        ratio=ratio,
        is_fixed_score=False,
        table_type=table_type,
    )


# ──────────────────────────────────────────────
# BC-26: BidAnalysisEngine — 통합 파이프라인
# ──────────────────────────────────────────────

class BidAnalysisEngine:
    """적격심사 가격점수 분석 통합 엔진.

    파이프라인:
      1. select_table → 별표 결정
      2. calculate_a_value → A값 합산
      3. ≥100억 early return
      4. check_net_cost_exclusion → 배제 판정
      5. calc_price_score → 가격점수 (배제여도 참고용 계산)
      6. final_pass 판정
      7. score_heatmap 생성
    """

    def __init__(
        self,
        estimated_price: int,
        work_type: WorkType,
        a_value_items: AValueItems,
        bid_price: Optional[int] = None,
        net_construction_cost: Optional[int] = None,
    ):
        if estimated_price <= 0:
            raise ValueError("estimated_price must be positive")
        if bid_price is not None and bid_price < 0:
            raise ValueError("bid_price must be non-negative")
        if net_construction_cost is not None and net_construction_cost < 0:
            raise ValueError("net_construction_cost must be non-negative")

        self.estimated_price = estimated_price
        self.work_type = work_type
        self.a_value_items = a_value_items
        self.bid_price = bid_price
        self.net_construction_cost = net_construction_cost

    def analyze(self) -> BidAnalysisResult:
        """분석 파이프라인 실행."""
        # Step 1: 별표 결정
        table_type = select_table(self.estimated_price, self.work_type)

        # Step 2: A값 합산
        a_value = calculate_a_value(self.a_value_items)

        # Step 3: ≥100억 early return
        if table_type == TableType.OUT_OF_SCOPE:
            return BidAnalysisResult(
                table_type=table_type,
                a_value=a_value,
                is_out_of_scope=True,
                final_pass=False,
                messages=["추정가격 100억 이상 — 적격심사 대상 외"],
            )

        result = BidAnalysisResult(
            table_type=table_type,
            a_value=a_value,
        )

        # A값 검증 (a_value >= estimated_price면 점수 계산 불가)
        if a_value >= self.estimated_price:
            result.final_pass = False
            result.messages.append(
                "A값이 추정가격 이상 — 가격점수 계산 불가"
            )
            return result

        # Step 4: 배제 판정
        if self.net_construction_cost is not None:
            if self.bid_price is not None:
                exclusion = check_net_cost_exclusion(
                    self.net_construction_cost, self.bid_price
                )
                result.exclusion_result = exclusion
                if exclusion.status == ExclusionStatus.EXCLUDED:
                    result.final_pass = False
                    result.messages.append(exclusion.message)
            else:
                result.exclusion_result = NetCostExclusionResult(
                    status=ExclusionStatus.NOT_CHECKED,
                    threshold=ceil_up(
                        Decimal(str(self.net_construction_cost))
                        * Decimal("98") / Decimal("100")
                    ),
                    message="투찰금액 미입력 — 배제 판정 보류",
                )
        else:
            result.exclusion_result = NetCostExclusionResult(
                status=ExclusionStatus.NOT_CHECKED,
                threshold=0,
                message="순공사원가 미입력 — 배제 판정 생략",
            )

        # Step 5: 가격점수 (배제여도 참고용 계산)
        if self.bid_price is not None:
            score_result = calc_price_score(
                self.bid_price, self.estimated_price, a_value, table_type
            )
            result.price_score_result = score_result

            if (result.exclusion_result
                    and result.exclusion_result.status == ExclusionStatus.EXCLUDED):
                # 배제 시 reference_price_score로 저장
                result.reference_price_score = score_result.score
                result.final_pass = False  # 강제
            else:
                result.reference_price_score = None

        # Step 6: final_pass 강제 (배제면 무조건 False)
        if (result.exclusion_result
                and result.exclusion_result.status == ExclusionStatus.EXCLUDED):
            result.final_pass = False

        # Step 7: 히트맵 생성
        result.score_heatmap = self._generate_score_heatmap(
            table_type, a_value
        )

        return result

    def _generate_score_heatmap(
        self,
        table_type: TableType,
        a_value: int,
    ) -> List[ScoreHeatmapPoint]:
        """Phase1 score_heatmap: 투찰률별 가격점수 테이블."""
        heatmap: List[ScoreHeatmapPoint] = []

        # 낙찰하한율 ~ 고정평점 비율 구간을 0.05%p 간격으로
        floor_rate = get_floor_rate(self.estimated_price)
        params = TABLE_PARAMS_MAP[table_type]

        # 범위: floor_rate% ~ fixed_ratio*100 + 1%
        start_pct = floor_rate  # 예: 89.745
        end_pct = params.fixed_ratio * Decimal("100") + Decimal("1")  # 예: 93.5

        est_d = Decimal(str(self.estimated_price))
        a_d = Decimal(str(a_value))

        step = Decimal("0.05")
        current = start_pct

        while current <= end_pct:
            rate = current / Decimal("100")
            bid_amount = ceil_up((est_d - a_d) * rate + a_d)

            score_result = calc_price_score(
                bid_amount, self.estimated_price, a_value, table_type
            )

            heatmap.append(ScoreHeatmapPoint(
                bid_rate=round_half_up(rate, 6),
                bid_amount=bid_amount,
                price_score=score_result.score,
                is_fixed_score=score_result.is_fixed_score,
            ))

            current += step

        return heatmap
