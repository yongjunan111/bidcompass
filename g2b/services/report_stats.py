"""BC-53: 유사공고 통계 조회.

presume_price 기준으로 유사한 낙찰 건의 투찰률 분포를 반환한다.
DB 집계(SQL)로 처리 — Python fetchall() 금지.
"""

from __future__ import annotations

import logging

from django.db import connection, transaction

logger = logging.getLogger(__name__)

_EMPTY_STATS = {
    "count": 0,
    "avg_bidder_cnt": 0,
    "p10_rate": 0.0,
    "p50_rate": 0.0,
    "p90_rate": 0.0,
}


def get_similar_bid_stats(presume_price: int) -> dict:
    """유사 공고의 낙찰 통계를 반환.

    1차 필터: presume_price ±15%, openg_rank='1', 최근 24개월.
    30건 미만이면 ±25%, 36개월로 확장.
    DB 에러 시 빈 결과 반환 (뷰 500 방지).

    Returns:
        dict(count, avg_bidder_cnt, p10_rate, p50_rate, p90_rate)
    """
    try:
        result = _query_stats(presume_price, pct=0.15, months=24)
        if result["count"] < 30:
            result = _query_stats(presume_price, pct=0.25, months=36)
        return result
    except Exception as e:
        logger.warning("get_similar_bid_stats failed: %s", e)
        return dict(_EMPTY_STATS)


def _query_stats(presume_price: int, pct: float, months: int) -> dict:
    """SQL로 통계를 직접 집계.

    - DISTINCT ON으로 공고당 1건만 (중복 제거)
    - openg_date는 BidContract 테이블에 존재
    - presume_price는 BidContract 테이블 사용
    """
    lower = int(presume_price * (1 - pct))
    upper = int(presume_price * (1 + pct))

    sql = f"""
        WITH rank1 AS (
            SELECT DISTINCT ON (br.bid_ntce_no, br.bid_ntce_ord)
                br.bid_rate,
                br.bidder_cnt
            FROM g2b_bidresult br
            JOIN g2b_bidcontract bc
                ON br.bid_ntce_no = bc.bid_ntce_no
                AND br.bid_ntce_ord = bc.bid_ntce_ord
            WHERE bc.presume_price BETWEEN %s AND %s
              AND br.openg_rank = '1'
              AND bc.openg_date >= TO_CHAR(
                  CURRENT_DATE - INTERVAL '{months} months', 'YYYYMMDD')
            ORDER BY br.bid_ntce_no, br.bid_ntce_ord
        )
        SELECT
            COUNT(*) AS cnt,
            COALESCE(AVG(bidder_cnt), 0) AS avg_bidder_cnt,
            COALESCE(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY bid_rate), 0) AS p10_rate,
            COALESCE(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY bid_rate), 0) AS p50_rate,
            COALESCE(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY bid_rate), 0) AS p90_rate
        FROM rank1
    """

    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(sql, [lower, upper])
        row = cursor.fetchone()

    if not row or row[0] == 0:
        return dict(_EMPTY_STATS)

    return {
        "count": row[0],
        "avg_bidder_cnt": round(float(row[1]), 1),
        "p10_rate": round(float(row[2]), 4),
        "p50_rate": round(float(row[3]), 4),
        "p90_rate": round(float(row[4]), 4),
    }
