"""BC-33: 규칙 기반 최적투찰 엔진.

복수예비가격 15개에서 C(15,4)=1,365개 예정가격 시나리오를 생성하고,
모든 시나리오에서 기대 가격점수를 최대화하는 투찰금액을 찾는다.

핵심 원칙:
  - 정답 데이터(실제 예정가격) 오염 없음 — 순수 규칙+수학만으로 추천
  - float 기반 빠른 스캔 + Decimal 기반 최종 검증
  - 3단계 계층적 스캔 (100K → 10K → 1K)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from typing import List, Optional, Tuple

from g2b.services.bid_engine import (
    TABLE_PARAMS_MAP,
    TableType,
    calc_price_score,
    ceil_up,
    get_floor_rate,
)
from decimal import Decimal


# ──────────────────────────────────────────────
# TABLE별 스캔 범위 / 밴드 임계값
# ──────────────────────────────────────────────

_SCAN_BOUNDS = {
    TableType.TABLE_1:  (0.85, 0.95),
    TableType.TABLE_2A: (0.87, 0.93),
    TableType.TABLE_2B: (0.87, 0.93),
    TableType.TABLE_3:  (0.89, 0.915),
    TableType.TABLE_4:  (0.89, 0.915),
    TableType.TABLE_5:  (0.89, 0.915),
}

_BAND_THRESHOLDS = {
    TableType.TABLE_1:  0.10,
    TableType.TABLE_2A: 0.05,
    TableType.TABLE_2B: 0.05,
    TableType.TABLE_3:  0.05,
    TableType.TABLE_4:  0.05,
    TableType.TABLE_5:  0.05,
}


# ──────────────────────────────────────────────
# 데이터 구조
# ──────────────────────────────────────────────

@dataclass
class OptimalBidInput:
    preliminary_prices: List[int]           # 복수예비가격 최대 15개 (bsisPlnprc)
    a_value: int                            # A값 합산
    table_type: TableType                   # select_table() 결과
    presume_price: int                      # 추정가격 (floor rate 계산용)
    net_construction_cost: Optional[int] = None  # 순공사원가 (있으면 하드 제약)


@dataclass
class OptimalBidResult:
    recommended_bid: int                    # 최적 투찰금액
    expected_score: float                   # 1,365 시나리오 기대점수
    n_scenarios: int                        # 시나리오 수
    min_scenario_score: float               # 최악 시나리오 점수
    max_scenario_score: float               # 최선 시나리오 점수
    scan_steps: int                         # 스캔한 투찰금액 수
    floor_bid: Optional[int]                # 하한 제약 (적용된 경우)
    floor_rate_bid: Optional[int] = None    # 하한율 최소 투찰가 (전 시나리오 통과)
    # BC-45: 3-strategy + band
    band_threshold: float = 0.05            # 밴드 임계값 (TABLE별 차등)
    band_low: int = 0                       # 밴드 하한
    band_high: int = 0                      # 밴드 상한
    safe_bid: Optional[int] = None          # 보수적 (band 내 최고 bid)
    aggressive_bid: Optional[int] = None    # 공격적 (band 내 최저 bid)


@dataclass
class EvalResult:
    score: float
    ratio: float
    is_fixed: bool


# ──────────────────────────────────────────────
# 반올림 헬퍼 (float 전용, 양수 전용)
# ──────────────────────────────────────────────

def _round_half_up_float(value: float, places: int) -> float:
    """사사오입 반올림 (양수 전용, float 기반).

    Python round()는 banker's rounding이므로 사용 금지.
    bid_engine.py:335의 round_half_up(ROUND_HALF_UP)과 동일 결과를 내기 위함.
    """
    m = 10 ** places
    return int(value * m + 0.5) / m


# ──────────────────────────────────────────────
# 1. generate_scenarios
# ──────────────────────────────────────────────

def generate_scenarios(prelim_prices: List[int]) -> List[int]:
    """복수예비가격에서 C(n,4) 예정가격 시나리오 생성.

    산식: 4개 평균 → floor (소수점 있을 때), int (정확히 나누어질 때).
    simulate_historical.py:824-825와 동일.

    Args:
        prelim_prices: 복수예비가격 리스트 (최소 4개)

    Returns:
        가능한 예정가격 리스트 (중복 포함)

    Raises:
        ValueError: 4개 미만일 때
    """
    n = len(prelim_prices)
    if n < 4:
        raise ValueError(
            f"복수예비가격 최소 4개 필요, {n}개 제공됨"
        )

    scenarios = []
    for combo in combinations(prelim_prices, 4):
        avg = sum(combo) / 4
        # floor 반올림: 정확히 나누어지면 int, 아니면 floor
        if avg != int(avg):
            scenarios.append(math.floor(avg))
        else:
            scenarios.append(int(avg))

    return scenarios


# ──────────────────────────────────────────────
# 2. _score_fast (float 기반 빠른 점수 계산)
# ──────────────────────────────────────────────

def _score_fast(
    bid: int,
    est: int,
    a: int,
    max_s: float,
    coeff: float,
    fixed_ratio: float,
    fixed_score: float,
) -> float:
    """float 기반 빠른 가격점수 계산 (스캔용).

    bid_engine.calc_price_score과 동일 로직, Decimal 없이.
    A >= est인 경우 score=2 반환 (ValueError 방지).
    """
    if a >= est:
        return 2.0

    ratio = _round_half_up_float((bid - a) / (est - a), 4)

    # 고정점수: bid <= est AND ratio >= fixed_ratio
    if bid <= est and ratio >= fixed_ratio:
        return fixed_score

    # 일반 공식: max - coeff * |90 - ratio * 100|
    score = max_s - coeff * abs(90.0 - ratio * 100.0)
    return max(score, 2.0)


# ──────────────────────────────────────────────
# 3. compute_expected_score
# ──────────────────────────────────────────────

def compute_expected_score(
    bid: int,
    scenarios: List[int],
    a: int,
    max_s: float,
    coeff: float,
    fixed_ratio: float,
    fixed_score: float,
) -> float:
    """모든 시나리오의 가격점수 평균 (등확률 1/N).

    Args:
        bid: 투찰금액
        scenarios: 예정가격 시나리오 리스트
        a: A값
        max_s, coeff, fixed_ratio, fixed_score: 별표 파라미터 (float)

    Returns:
        기대 가격점수
    """
    total = 0.0
    for est in scenarios:
        total += _score_fast(bid, est, a, max_s, coeff, fixed_ratio, fixed_score)
    return total / len(scenarios)


# ──────────────────────────────────────────────
# 4. find_optimal_bid
# ──────────────────────────────────────────────

def find_optimal_bid(inp: OptimalBidInput) -> OptimalBidResult:
    """3단계 계층적 스캔으로 최적 투찰금액 탐색.

    Phase 1: step=100,000원 (전체 범위)
    Phase 2: step=10,000원 (Phase 1 최적 ±100,000원)
    Phase 3: step=1,000원 (Phase 2 최적 ±10,000원)
    """
    if inp.table_type == TableType.OUT_OF_SCOPE:
        raise ValueError("OUT_OF_SCOPE는 최적투찰 대상이 아님")

    scenarios = generate_scenarios(inp.preliminary_prices)
    n_scenarios = len(scenarios)

    # 별표 파라미터 (float 변환)
    params = TABLE_PARAMS_MAP[inp.table_type]
    max_s = float(params.max_score)
    coeff = float(params.coeff)
    fixed_ratio = float(params.fixed_ratio)
    fixed_score = float(params.fixed_score)

    # 스캔 범위 결정 (BC-45: TABLE별 차등)
    min_est = min(scenarios)
    max_est = max(scenarios)
    a = inp.a_value

    lb, ub = _SCAN_BOUNDS[inp.table_type]
    scan_lower = int(a + lb * (min_est - a))
    scan_upper = int(a + ub * (max_est - a))

    # 하드 제약: 순공사원가 × 98%
    floor_bid = None
    if inp.net_construction_cost is not None:
        floor_bid = math.ceil(inp.net_construction_cost * 0.98)
        scan_lower = max(scan_lower, floor_bid)

    # 최소한의 범위 보장
    if scan_lower >= scan_upper:
        scan_upper = scan_lower + 100_000

    total_steps = 0

    def _scan(lo: int, hi: int, step: int) -> Tuple[int, float]:
        nonlocal total_steps
        best_bid = lo
        best_score = -1.0
        bid = lo
        while bid <= hi:
            s = compute_expected_score(
                bid, scenarios, a, max_s, coeff, fixed_ratio, fixed_score,
            )
            total_steps += 1
            if s > best_score:
                best_score = s
                best_bid = bid
            bid += step
        return best_bid, best_score

    # Phase 1: 100K step
    best1, _ = _scan(scan_lower, scan_upper, 100_000)

    # Phase 2: 10K step, ±100K around Phase 1 best
    lo2 = max(scan_lower, best1 - 100_000)
    hi2 = min(scan_upper, best1 + 100_000)
    best2, _ = _scan(lo2, hi2, 10_000)

    # Phase 3: 1K step, ±10K around Phase 2 best
    lo3 = max(scan_lower, best2 - 10_000)
    hi3 = min(scan_upper, best2 + 10_000)
    best3, best_expected = _scan(lo3, hi3, 1_000)

    # 최종 추천 bid
    recommended_bid = best3

    # 하한 제약 적용
    if floor_bid is not None and recommended_bid < floor_bid:
        recommended_bid = floor_bid

    # 최종 기대점수 재계산 (최종 bid로)
    final_expected = compute_expected_score(
        recommended_bid, scenarios, a, max_s, coeff, fixed_ratio, fixed_score,
    )

    # 시나리오별 최선/최악 점수
    scores = [
        _score_fast(recommended_bid, est, a, max_s, coeff, fixed_ratio, fixed_score)
        for est in scenarios
    ]

    # 하한율 최소 투찰가 (전 시나리오 통과)
    floor_rate = get_floor_rate(inp.presume_price)
    max_scenario_est = max(scenarios)
    floor_rate_bid = math.ceil(a + float(floor_rate) / 100 * (max_scenario_est - a))

    # BC-45: 밴드 + 3-strategy 계산
    band_threshold = _BAND_THRESHOLDS[inp.table_type]
    threshold = final_expected - band_threshold

    # floor 제약: floor_bid(순공사원가 98%)와 floor_rate_bid 중 큰 값
    band_floor = max(
        floor_bid or 0,
        floor_rate_bid,
    )

    band_bids = []
    for offset in range(-100, 101):
        test_bid = recommended_bid + offset * 1_000
        if test_bid <= 0 or test_bid < band_floor:
            continue
        es = compute_expected_score(
            test_bid, scenarios, a, max_s, coeff, fixed_ratio, fixed_score,
        )
        if es >= threshold:
            band_bids.append(test_bid)

    band_low = min(band_bids) if band_bids else recommended_bid
    band_high = max(band_bids) if band_bids else recommended_bid
    safe_bid = band_high if band_high != recommended_bid else None
    aggressive_bid = band_low if band_low != recommended_bid else None

    return OptimalBidResult(
        recommended_bid=recommended_bid,
        expected_score=final_expected,
        n_scenarios=n_scenarios,
        min_scenario_score=min(scores),
        max_scenario_score=max(scores),
        scan_steps=total_steps,
        floor_bid=floor_bid,
        floor_rate_bid=floor_rate_bid,
        band_threshold=band_threshold,
        band_low=band_low,
        band_high=band_high,
        safe_bid=safe_bid,
        aggressive_bid=aggressive_bid,
    )


# ──────────────────────────────────────────────
# 5. evaluate_bid
# ──────────────────────────────────────────────

def evaluate_bid(
    bid: int,
    actual_est_price: int,
    a_value: int,
    table_type: TableType,
) -> EvalResult:
    """실제 예정가격이 밝혀진 후, bid의 실제 가격점수 계산.

    Decimal 기반 calc_price_score 호출 (정밀 검증용).
    A >= est인 경우 score=2, ratio=0 반환 (calc_price_score의 ValueError 방지).
    """
    if table_type == TableType.OUT_OF_SCOPE:
        return EvalResult(score=2.0, ratio=0.0, is_fixed=False)

    # A >= est 사전 검사 (bid_engine.py:324의 ValueError 방지)
    if a_value >= actual_est_price:
        return EvalResult(score=2.0, ratio=0.0, is_fixed=False)

    result = calc_price_score(bid, actual_est_price, a_value, table_type)
    return EvalResult(
        score=float(result.score),
        ratio=float(result.ratio),
        is_fixed=result.is_fixed_score,
    )
