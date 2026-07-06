"""시장 세그먼트 정책 조회 서비스.

analyze_cross_table M8 산출물(segment_policy_v1.json, 2026-03-03 생성)의
스냅샷(`g2b/resources/segment_policy_v1.json`)을 읽어, 별표(TableType) ×
경쟁강도(예상 참가자수 버킷) 세그먼트별 시장 투찰 정책을 반환한다.

ratio 단위: bid_amt / estimated_price(예정가격) × 100 (%).

품질 게이트를 하나라도 통과하지 못하면 None을 반환해 기존 90% 기본 추천으로
폴백한다. 파일 없음/파싱 실패 등 어떤 경우에도 서빙으로 예외를 올리지 않는다.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from g2b.services.bid_engine import TableType, get_floor_rate

logger = logging.getLogger(__name__)

# 정책 스냅샷 경로 (g2b/resources/segment_policy_v1.json)
_POLICY_PATH = Path(__file__).resolve().parent.parent / 'resources' / 'segment_policy_v1.json'

# TableType → price_seg 매핑 (별표 2-나 / 대상외는 정책 세그먼트 없음)
_PRICE_SEG_MAP = {
    TableType.TABLE_1: 'T1',
    TableType.TABLE_2A: 'T2A',
    TableType.TABLE_3: 'T3',
    TableType.TABLE_4: 'T4',
    TableType.TABLE_5: 'T5',
}

# 품질 게이트 기준
_MIN_CONFIDENCE = 0.5   # 세그먼트 신뢰도 하한
_MIN_SAMPLE_N = 1000    # 표본 수 하한


@dataclass(frozen=True)
class MarketPolicy:
    """세그먼트별 시장 투찰 정책 (단위: bid/예정가격 %)."""

    segment_id: str
    center: float
    ratio_low: float
    ratio_high: float
    confidence: float
    sample_n: int


def _comp_seg(expected_bidder_cnt: Optional[float]) -> Optional[str]:
    """예상 참가자수 → 경쟁강도 버킷. None 또는 0 이하 → None."""
    if expected_bidder_cnt is None or expected_bidder_cnt <= 0:
        return None
    if expected_bidder_cnt < 10:
        return 'C01_09'
    if expected_bidder_cnt < 30:
        return 'C10_29'
    if expected_bidder_cnt < 50:
        return 'C30_49'
    if expected_bidder_cnt < 100:
        return 'C50_99'
    if expected_bidder_cnt < 200:
        return 'C100_199'
    return 'C200+'


@lru_cache(maxsize=1)
def _load_policy_map() -> Optional[dict]:
    """정책 JSON을 1회 로드해 segment_id → row dict로 반환. 실패 시 None."""
    try:
        with open(_POLICY_PATH, encoding='utf-8') as f:
            rows = json.load(f)
        return {row['segment_id']: row for row in rows}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        logger.warning('세그먼트 정책 로드 실패 (%s): %s', _POLICY_PATH, exc)
        return None


def get_market_policy(
    table_type: TableType,
    expected_bidder_cnt: Optional[float],
    estimated_price: int,
) -> Optional[MarketPolicy]:
    """세그먼트 시장 정책 조회. 게이트 미통과/조회 실패 시 None (폴백).

    게이트 (하나라도 실패 → None):
      1. confidence >= 0.5
      2. sample_n >= 1000
      3. center <= ratio_high (center > high는 데이터 이상 → 폴백;
         center < ratio_low는 허용 — floor 클램프가 처리)
      4. ratio_high >= 낙찰하한율 (시장 밴드 전체가 하한율 아래면
         모집단 오염 의심 → 폴백)
    """
    price_seg = _PRICE_SEG_MAP.get(table_type)
    if price_seg is None:
        return None

    comp_seg = _comp_seg(expected_bidder_cnt)
    if comp_seg is None:
        return None

    if estimated_price is None or estimated_price <= 0:
        logger.warning('세그먼트 정책 조회 불가: estimated_price=%s', estimated_price)
        return None

    policy_map = _load_policy_map()
    if policy_map is None:
        return None

    segment_id = f'{price_seg}_{comp_seg}'
    row = policy_map.get(segment_id)
    if row is None:
        logger.warning('세그먼트 정책 없음: %s', segment_id)
        return None

    try:
        center = float(row['center'])
        ratio_low = float(row['ratio_low'])
        ratio_high = float(row['ratio_high'])
        confidence = float(row['confidence'])
        sample_n = int(row['sample_n'])
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning('세그먼트 정책 필드 이상 (%s): %s', segment_id, exc)
        return None

    # 게이트 1: 신뢰도
    if confidence < _MIN_CONFIDENCE:
        return None
    # 게이트 2: 표본 수
    if sample_n < _MIN_SAMPLE_N:
        return None
    # 게이트 3: center가 밴드 상단 초과 → 데이터 이상
    if center > ratio_high:
        return None
    # 게이트 4: 시장 밴드 전체가 낙찰하한율 아래 → 모집단 오염 의심
    if ratio_high < float(get_floor_rate(estimated_price)):
        return None

    return MarketPolicy(
        segment_id=segment_id,
        center=center,
        ratio_low=ratio_low,
        ratio_high=ratio_high,
        confidence=confidence,
        sample_n=sample_n,
    )
