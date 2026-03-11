"""사전 투찰 추천 서비스.

복수예비가격 없이 기초금액 기반으로 최적 투찰금액을 추천한다.
시나리오 시뮬레이션 없이, 순수 수학적 계산.

핵심 원리:
  - 예정가격 ≈ 기초금액 (복수예비가격은 기초금액 ±3%, 4개 평균)
  - 최적 투찰 비율 = 90% (기준율)
  - optimal_bid = A + 0.90 × (기초금액 - A)
  - 밴드: TABLE별 coeff로 직접 계산 (2점 허용 범위)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from g2b.services.bid_engine import (
    TABLE_PARAMS_MAP,
    TableType,
    get_floor_rate,
)

# TABLE별 밴드 허용 점수 하락폭 (2점 = 실전적 허용 범위)
# coeff 2  → ±1.0%p,  coeff 4 → ±0.5%p,  coeff 20 → ±0.1%p
_BAND_SCORE_TOLERANCE = 2.0

_TABLE_LABELS = {
    TableType.TABLE_1: '별표 1',
    TableType.TABLE_2A: '별표 2-가',
    TableType.TABLE_2B: '별표 2-나',
    TableType.TABLE_3: '별표 3',
    TableType.TABLE_4: '별표 4',
    TableType.TABLE_5: '별표 5',
}


@dataclass
class PreBidResult:
    optimal_bid: int            # 최적 투찰금액 (ratio 90%)
    optimal_score: float        # TABLE 만점
    safe_bid: int               # 보수적 (밴드 상단, 높은 금액)
    aggressive_bid: int         # 공격적 (밴드 하단, 낮은 금액)
    band_low: int               # 밴드 하한
    band_high: int              # 밴드 상한
    band_half_width: float      # 밴드 반폭 (%p)
    floor_rate: float           # 하한율 (%)
    floor_rate_bid: int         # 하한 최소 투찰가
    floor_rate_pass: bool       # 최적 투찰가 하한율 통과 여부
    table_label: str            # 별표 표시명


def prebid_recommend(
    base_amount: int,
    a_value: int,
    table_type: TableType,
    presume_price: int,
    net_construction_cost: Optional[int] = None,
) -> PreBidResult:
    """사전 투찰 추천.

    기초금액 기반으로 최적 투찰금액과 safe/aggressive 밴드를 계산한다.
    복수예비가격이나 시나리오 시뮬레이션 없음.
    """
    if table_type == TableType.OUT_OF_SCOPE:
        raise ValueError("OUT_OF_SCOPE는 추천 대상이 아님")

    est = base_amount  # 예정가격 ≈ 기초금액
    a = a_value

    if a >= est:
        raise ValueError("A값이 기초금액 이상이면 추천 불가")

    params = TABLE_PARAMS_MAP[table_type]
    max_score = float(params.max_score)
    coeff = float(params.coeff)

    # ── 1) 최적 투찰금액: ratio 0.9000 ──
    optimal_bid = round(a + 0.9 * (est - a))

    # ── 2) 밴드 계산 ──
    # score = max - coeff * |90 - ratio*100|
    # |90 - ratio*100| ≤ tolerance / coeff
    half_width_pct = _BAND_SCORE_TOLERANCE / coeff  # %p 단위

    band_ratio_low = (90.0 - half_width_pct) / 100.0
    band_ratio_high = (90.0 + half_width_pct) / 100.0

    band_low_raw = round(a + band_ratio_low * (est - a))
    band_high_raw = round(a + band_ratio_high * (est - a))

    # ── 3) 하한율 ──
    floor_rate = get_floor_rate(presume_price)
    floor_rate_bid = math.ceil(a + float(floor_rate) / 100 * (est - a))

    # ── 4) 하드 제약: 순공사원가 × 98% ──
    floor_bid = None
    if net_construction_cost is not None:
        floor_bid = math.ceil(net_construction_cost * 0.98)

    # ── 5) 바닥 제약 적용 ──
    effective_floor = max(floor_bid or 0, floor_rate_bid)
    band_low = max(band_low_raw, effective_floor)
    band_high = band_high_raw

    # ── 6) safe / aggressive ──
    safe_bid = band_high
    aggressive_bid = band_low

    # 최적 bid가 바닥 미달이면 바닥으로 올림
    if optimal_bid < effective_floor:
        optimal_bid = effective_floor

    floor_rate_pass = optimal_bid >= floor_rate_bid

    return PreBidResult(
        optimal_bid=optimal_bid,
        optimal_score=max_score,
        safe_bid=safe_bid,
        aggressive_bid=aggressive_bid,
        band_low=band_low,
        band_high=band_high,
        band_half_width=half_width_pct,
        floor_rate=float(floor_rate),
        floor_rate_bid=floor_rate_bid,
        floor_rate_pass=floor_rate_pass,
        table_label=_TABLE_LABELS.get(table_type, str(table_type)),
    )
