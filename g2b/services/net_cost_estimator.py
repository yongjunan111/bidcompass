"""순공사원가 추정 모듈.

기초금액 대비 비율로 순공사원가를 추정한다.
2,253건 실데이터 분석 기반 (중앙값 84.2%, 표준편차 4.4%p).
"""

import math

# 구간별 중앙값 비율 (기초금액 대비)
# 전체 중앙값 84.2%로 충분히 안정적이지만, 구간별로도 제공
NET_COST_RATIO_TABLE = {
    'under_10': 0.841,   # 10억 미만 (1,360건)
    '10_to_30': 0.841,   # 10~30억 (650건)
    '30_to_50': 0.839,   # 30~50억 (127건)
    '50_to_100': 0.862,  # 50~100억 (116건)
}

DEFAULT_RATIO = 0.842  # 전체 중앙값


def estimate_net_construction_cost(base_amount: int) -> dict:
    """기초금액으로 순공사원가 추정.

    Returns:
        dict with keys:
        - estimated_net_cost: int (추정 순공사원가)
        - ratio_used: float (적용된 비율)
        - threshold_98: int (순공사원가 × 98% = 실질 바닥가)
        - is_estimated: True (추정값임을 표시)
    """
    if base_amount < 1_000_000_000:
        ratio = NET_COST_RATIO_TABLE['under_10']
    elif base_amount < 3_000_000_000:
        ratio = NET_COST_RATIO_TABLE['10_to_30']
    elif base_amount < 5_000_000_000:
        ratio = NET_COST_RATIO_TABLE['30_to_50']
    else:
        ratio = NET_COST_RATIO_TABLE['50_to_100']

    estimated = int(base_amount * ratio)
    threshold = math.ceil(estimated * 0.98)

    return {
        'estimated_net_cost': estimated,
        'ratio_used': ratio,
        'threshold_98': threshold,
        'is_estimated': True,
    }
