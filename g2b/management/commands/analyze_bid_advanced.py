"""추가 EDA: 투찰 전략 + 시장 구조 + 제품 직결 분석.

기존 analyze_bid_distribution에서 다루지 않은 관점:
  - 투찰 전략: 1순위-2순위 gap, round number bias, 반복 투찰 패턴
  - 시장 구조: 월별 트렌드, 참여자 수 분포, 가격대 세분화
  - 제품 직결: 하한율 근처 탈락, 기준율 근처 밀집도

전부 SQL 집계 — 8GB RAM에서 32M건 안전하게 처리.

사용:
    python manage.py analyze_bid_advanced
    python manage.py analyze_bid_advanced --output data/collected/bid_advanced_eda.json
"""

import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UNIT_EOUK = 1_0000_0000
REGULATION_DATE = "20260130"


class Command(BaseCommand):
    help = "추가 EDA: 투찰 전략 + 시장 구조 + 제품 직결 분석"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로",
        )

    def handle(self, *args, **options):
        output_path = options["output"]
        results = {}

        self.stdout.write("=" * 60)
        self.stdout.write("  추가 EDA: 투찰 전략 + 시장 구조 + 제품 직결 분석")
        self.stdout.write("=" * 60)

        # ── 투찰 전략 분석 ──
        self.stdout.write("\n[1] 1순위 vs 2순위 투찰비율 gap 분석...")
        results["rank_gap"] = self._analyze_rank_gap()
        self._print_rank_gap(results["rank_gap"])

        self.stdout.write("\n[2] Round number bias 분석...")
        results["round_number"] = self._analyze_round_number_bias()
        self._print_round_number(results["round_number"])

        self.stdout.write("\n[3] 동일 업체 반복 투찰 패턴...")
        results["repeat_bidder"] = self._analyze_repeat_bidder()
        self._print_repeat_bidder(results["repeat_bidder"])

        # ── 시장 구조 분석 ──
        self.stdout.write("\n[4] 월별 투찰비율 트렌드...")
        results["monthly_trend"] = self._analyze_monthly_trend()
        self._print_monthly_trend(results["monthly_trend"])

        self.stdout.write("\n[5] 공고당 참여자 수 분포...")
        results["bidder_count_dist"] = self._analyze_bidder_count_dist()
        self._print_bidder_count_dist(results["bidder_count_dist"])

        self.stdout.write("\n[6] 가격대 세분화 (1억 단위)...")
        results["price_segment"] = self._analyze_price_segment()
        self._print_price_segment(results["price_segment"])

        # ── 제품 직결 분석 ──
        self.stdout.write("\n[7] 낙찰하한율 근처 탈락 분석...")
        results["threshold_risk"] = self._analyze_threshold_risk()
        self._print_threshold_risk(results["threshold_risk"])

        self.stdout.write("\n[8] 기준율 90% 근처 밀집도...")
        results["base_rate_density"] = self._analyze_base_rate_density()
        self._print_base_rate_density(results["base_rate_density"])

        # ── JSON 저장 ──
        if output_path:
            self._save_json(results, output_path)

    # ═══════════════════════════════════════════
    # 1. 1순위 vs 2순위 gap
    # ═══════════════════════════════════════════

    def _analyze_rank_gap(self) -> dict:
        sql = f"""
            WITH ranked AS (
                SELECT
                    bid_ntce_no, bid_ntce_ord,
                    openg_rank,
                    bid_amt::float / estimated_price * 100 AS ratio
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND openg_rank IN ('1', '2')
            ),
            paired AS (
                SELECT
                    r1.bid_ntce_no, r1.bid_ntce_ord,
                    r1.ratio AS rank1_ratio,
                    r2.ratio AS rank2_ratio,
                    ABS(r1.ratio - r2.ratio) AS gap
                FROM ranked r1
                JOIN ranked r2
                    ON r1.bid_ntce_no = r2.bid_ntce_no
                   AND r1.bid_ntce_ord = r2.bid_ntce_ord
                WHERE r1.openg_rank = '1' AND r2.openg_rank = '2'
            )
            SELECT
                COUNT(*) AS n,
                AVG(gap) AS mean_gap,
                STDDEV_POP(gap) AS std_gap,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY gap) AS p50_gap,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY gap) AS p90_gap,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY gap) AS p95_gap,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY gap) AS p99_gap,
                SUM(CASE WHEN gap < 0.01 THEN 1 ELSE 0 END) AS gap_lt_001,
                SUM(CASE WHEN gap < 0.05 THEN 1 ELSE 0 END) AS gap_lt_005,
                SUM(CASE WHEN gap < 0.1 THEN 1 ELSE 0 END) AS gap_lt_01,
                SUM(CASE WHEN gap < 0.5 THEN 1 ELSE 0 END) AS gap_lt_05,
                SUM(CASE WHEN gap < 1.0 THEN 1 ELSE 0 END) AS gap_lt_1
            FROM paired
        """
        # gap 히스토그램
        hist_sql = f"""
            WITH ranked AS (
                SELECT
                    bid_ntce_no, bid_ntce_ord, openg_rank,
                    bid_amt::float / estimated_price * 100 AS ratio
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND openg_rank IN ('1', '2')
            ),
            paired AS (
                SELECT ABS(r1.ratio - r2.ratio) AS gap
                FROM ranked r1
                JOIN ranked r2
                    ON r1.bid_ntce_no = r2.bid_ntce_no
                   AND r1.bid_ntce_ord = r2.bid_ntce_ord
                WHERE r1.openg_rank = '1' AND r2.openg_rank = '2'
            )
            SELECT
                FLOOR(gap / 0.05) * 0.05 AS bin_lo,
                COUNT(*) AS cnt
            FROM paired
            WHERE gap < 2.0
            GROUP BY bin_lo
            ORDER BY bin_lo
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            cols = [c[0] for c in cursor.description]
            stats = dict(zip(cols, row))

            cursor.execute(hist_sql)
            hist = [{"lo": round(float(r[0]), 2), "cnt": r[1]} for r in cursor.fetchall()]

        stats["histogram"] = hist
        return stats

    def _print_rank_gap(self, data: dict):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 1: 1순위 vs 2순위 투찰비율 gap")
        self.stdout.write("=" * 60)
        n = data["n"]
        self.stdout.write(f"  총 {n:,}건 (1·2순위 페어)")
        self.stdout.write(
            f"  평균 gap: {float(data['mean_gap']):.4f}%p"
            f"  σ: {float(data['std_gap']):.4f}%p"
            f"  P50: {float(data['p50_gap']):.4f}%p"
        )
        self.stdout.write(f"\n  근소차 낙찰 비율:")
        self.stdout.write(f"    gap < 0.01%p: {data['gap_lt_001']:,}건 ({data['gap_lt_001']/n*100:.1f}%)")
        self.stdout.write(f"    gap < 0.05%p: {data['gap_lt_005']:,}건 ({data['gap_lt_005']/n*100:.1f}%)")
        self.stdout.write(f"    gap < 0.1%p:  {data['gap_lt_01']:,}건 ({data['gap_lt_01']/n*100:.1f}%)")
        self.stdout.write(f"    gap < 0.5%p:  {data['gap_lt_05']:,}건 ({data['gap_lt_05']/n*100:.1f}%)")
        self.stdout.write(f"    gap < 1.0%p:  {data['gap_lt_1']:,}건 ({data['gap_lt_1']/n*100:.1f}%)")

        self.stdout.write(f"\n  gap 히스토그램 (0.05%p 단위, ~2%p):")
        max_c = max(h["cnt"] for h in data["histogram"]) if data["histogram"] else 1
        for h in data["histogram"][:20]:
            bar = "▓" * int(h["cnt"] / max_c * 30)
            self.stdout.write(f"    {h['lo']:5.2f}~{h['lo']+0.05:<5.2f}: {h['cnt']:>7,}건  {bar}")

    # ═══════════════════════════════════════════
    # 2. Round number bias
    # ═══════════════════════════════════════════

    def _analyze_round_number_bias(self) -> dict:
        sql = f"""
            WITH bid_data AS (
                SELECT
                    bid_amt::float / estimated_price * 100 AS ratio,
                    CASE WHEN openg_rank = '1' THEN true ELSE false END AS is_rank1
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND bid_amt::float / estimated_price * 100 BETWEEN 85 AND 95
            )
            SELECT
                ROUND(ratio::numeric, 2) AS ratio_2d,
                COUNT(*) AS total_cnt,
                SUM(CASE WHEN is_rank1 THEN 1 ELSE 0 END) AS rank1_cnt
            FROM bid_data
            GROUP BY ratio_2d
            ORDER BY total_cnt DESC
            LIMIT 50
        """
        # 특정 round number 근처 밀집
        round_sql = f"""
            WITH bid_data AS (
                SELECT
                    bid_amt::float / estimated_price * 100 AS ratio
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND bid_amt::float / estimated_price * 100 BETWEEN 85 AND 95
            )
            SELECT
                target,
                SUM(CASE WHEN ABS(ratio - target) < 0.005 THEN 1 ELSE 0 END) AS exact_cnt,
                SUM(CASE WHEN ABS(ratio - target) < 0.05 THEN 1 ELSE 0 END) AS near_cnt,
                COUNT(*) AS total
            FROM bid_data,
                 (VALUES (86.0),(87.0),(87.745),(88.0),(88.745),(89.0),(89.745),(90.0),(90.2),(91.0),(92.0),(95.0)) AS targets(target)
            GROUP BY target
            ORDER BY target
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            top_ratios = [
                {"ratio": float(r[0]), "total": r[1], "rank1": r[2]}
                for r in cursor.fetchall()
            ]

            cursor.execute(round_sql)
            cols = [c[0] for c in cursor.description]
            round_numbers = [dict(zip(cols, r)) for r in cursor.fetchall()]

        return {"top_ratios": top_ratios, "round_numbers": round_numbers}

    def _print_round_number(self, data: dict):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 2: Round Number Bias (가장 많이 찍히는 비율)")
        self.stdout.write("=" * 60)
        self.stdout.write("  [상위 20 투찰비율 (0.01% 단위)]")
        for i, r in enumerate(data["top_ratios"][:20], 1):
            self.stdout.write(
                f"    {i:>2}. {r['ratio']:7.2f}%  "
                f"전체 {r['total']:>8,}건  낙찰 {r['rank1']:>6,}건"
            )

        self.stdout.write("\n  [주요 라운드 넘버 근처 밀집]")
        self.stdout.write(f"    {'비율':>10s}  {'정확(±0.005)':>12s}  {'근처(±0.05)':>12s}")
        self.stdout.write("    " + "-" * 40)
        for r in data["round_numbers"]:
            self.stdout.write(
                f"    {float(r['target']):>10.3f}%  "
                f"{r['exact_cnt']:>10,}건  "
                f"{r['near_cnt']:>10,}건"
            )

    # ═══════════════════════════════════════════
    # 3. 동일 업체 반복 투찰
    # ═══════════════════════════════════════════

    def _analyze_repeat_bidder(self) -> dict:
        sql = f"""
            WITH bidder_stats AS (
                SELECT
                    company_bizno,
                    COUNT(*) AS bid_count,
                    AVG(bid_amt::float / estimated_price * 100) AS avg_ratio,
                    STDDEV_POP(bid_amt::float / estimated_price * 100) AS std_ratio,
                    SUM(CASE WHEN openg_rank = '1' THEN 1 ELSE 0 END) AS win_count
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND company_bizno != ''
                  AND bid_amt::float / estimated_price * 100 BETWEEN 70 AND 110
                GROUP BY company_bizno
            )
            SELECT
                CASE
                    WHEN bid_count = 1 THEN '1회'
                    WHEN bid_count BETWEEN 2 AND 5 THEN '2~5회'
                    WHEN bid_count BETWEEN 6 AND 20 THEN '6~20회'
                    WHEN bid_count BETWEEN 21 AND 100 THEN '21~100회'
                    ELSE '100+회'
                END AS group_label,
                COUNT(*) AS company_count,
                AVG(bid_count) AS avg_bids,
                AVG(avg_ratio) AS avg_ratio,
                AVG(std_ratio) AS avg_std,
                AVG(CASE WHEN bid_count > 1 THEN win_count::float / bid_count ELSE NULL END) AS avg_win_rate
            FROM bidder_stats
            GROUP BY
                CASE
                    WHEN bid_count = 1 THEN '1회'
                    WHEN bid_count BETWEEN 2 AND 5 THEN '2~5회'
                    WHEN bid_count BETWEEN 6 AND 20 THEN '6~20회'
                    WHEN bid_count BETWEEN 21 AND 100 THEN '21~100회'
                    ELSE '100+회'
                END
            ORDER BY MIN(bid_count)
        """
        # 다빈도 업체의 σ 분포
        sigma_sql = f"""
            WITH bidder_stats AS (
                SELECT
                    company_bizno,
                    COUNT(*) AS bid_count,
                    STDDEV_POP(bid_amt::float / estimated_price * 100) AS std_ratio
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND company_bizno != ''
                  AND bid_amt::float / estimated_price * 100 BETWEEN 70 AND 110
                GROUP BY company_bizno
                HAVING COUNT(*) >= 10
            )
            SELECT
                CASE
                    WHEN std_ratio < 0.5 THEN 'σ<0.5 (고정패턴)'
                    WHEN std_ratio < 1.0 THEN '0.5≤σ<1.0'
                    WHEN std_ratio < 2.0 THEN '1.0≤σ<2.0'
                    ELSE 'σ≥2.0 (분산큼)'
                END AS sigma_group,
                COUNT(*) AS company_count,
                AVG(bid_count) AS avg_bids,
                AVG(std_ratio) AS avg_std
            FROM bidder_stats
            GROUP BY
                CASE
                    WHEN std_ratio < 0.5 THEN 'σ<0.5 (고정패턴)'
                    WHEN std_ratio < 1.0 THEN '0.5≤σ<1.0'
                    WHEN std_ratio < 2.0 THEN '1.0≤σ<2.0'
                    ELSE 'σ≥2.0 (분산큼)'
                END
            ORDER BY MIN(std_ratio)
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c[0] for c in cursor.description]
            groups = [dict(zip(cols, r)) for r in cursor.fetchall()]

            cursor.execute(sigma_sql)
            cols2 = [c[0] for c in cursor.description]
            sigma = [dict(zip(cols2, r)) for r in cursor.fetchall()]

        return {"groups": groups, "sigma_distribution": sigma}

    def _print_repeat_bidder(self, data: dict):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 3: 동일 업체 반복 투찰 패턴")
        self.stdout.write("=" * 60)
        self.stdout.write(
            f"  {'그룹':>10s}  {'업체수':>8s}  {'평균투찰':>8s}  "
            f"{'평균비율':>8s}  {'평균σ':>7s}  {'낙찰률':>7s}"
        )
        self.stdout.write("  " + "-" * 60)
        for g in data["groups"]:
            win_rate = f"{float(g['avg_win_rate'])*100:.1f}%" if g["avg_win_rate"] else "N/A"
            self.stdout.write(
                f"  {g['group_label']:>10s}  {g['company_count']:>8,}  "
                f"{float(g['avg_bids']):>8.1f}  "
                f"{float(g['avg_ratio']):>8.2f}%  "
                f"{float(g['avg_std'] or 0):>7.2f}  "
                f"{win_rate:>7s}"
            )

        self.stdout.write(f"\n  [10회+ 투찰 업체의 σ 분포]")
        for s in data["sigma_distribution"]:
            self.stdout.write(
                f"    {s['sigma_group']:<20s}: "
                f"{s['company_count']:>6,}개 업체  "
                f"평균 {float(s['avg_bids']):.0f}회 투찰  "
                f"평균 σ={float(s['avg_std']):.2f}%"
            )

    # ═══════════════════════════════════════════
    # 4. 월별 트렌드
    # ═══════════════════════════════════════════

    def _analyze_monthly_trend(self) -> dict:
        sql = f"""
            WITH monthly AS (
                SELECT
                    SUBSTRING(c.openg_date, 1, 6) AS month,
                    COUNT(DISTINCT (r.bid_ntce_no, r.bid_ntce_ord)) AS announcement_cnt,
                    COUNT(*) AS bid_cnt,
                    AVG(CASE WHEN r.openg_rank = '1' THEN r.bid_amt::float / r.estimated_price * 100 END) AS rank1_avg,
                    STDDEV_POP(CASE WHEN r.openg_rank = '1' THEN r.bid_amt::float / r.estimated_price * 100 END) AS rank1_std,
                    AVG(r.bid_amt::float / r.estimated_price * 100) AS total_avg,
                    AVG(r.bidder_cnt) AS avg_bidder_cnt
                FROM g2b_bidresult r
                JOIN (
                    SELECT DISTINCT ON (bid_ntce_no, bid_ntce_ord)
                        bid_ntce_no, bid_ntce_ord, openg_date
                    FROM g2b_bidcontract
                    WHERE openg_date != '' AND LENGTH(openg_date) >= 6
                    ORDER BY bid_ntce_no, bid_ntce_ord
                ) c ON r.bid_ntce_no = c.bid_ntce_no AND r.bid_ntce_ord = c.bid_ntce_ord
                WHERE r.presume_price > 0 AND r.presume_price < {100 * UNIT_EOUK}
                  AND r.estimated_price > 0 AND r.bid_amt > 0
                  AND r.bid_amt::float / r.estimated_price * 100 BETWEEN 70 AND 110
                GROUP BY month
                HAVING COUNT(*) > 100
            )
            SELECT * FROM monthly ORDER BY month
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, r)) for r in cursor.fetchall()]

    def _print_monthly_trend(self, data: list):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 4: 월별 투찰비율 트렌드")
        self.stdout.write("=" * 60)
        self.stdout.write(
            f"  {'월':>8s}  {'공고수':>7s}  {'투찰건':>9s}  "
            f"{'낙찰자평균':>8s}  {'낙찰자σ':>7s}  {'전체평균':>8s}  {'평균참여':>7s}"
        )
        self.stdout.write("  " + "-" * 70)
        for r in data:
            self.stdout.write(
                f"  {r['month']:>8s}  {r['announcement_cnt']:>7,}  {r['bid_cnt']:>9,}  "
                f"{float(r['rank1_avg'] or 0):>8.2f}%  "
                f"{float(r['rank1_std'] or 0):>7.2f}  "
                f"{float(r['total_avg'] or 0):>8.2f}%  "
                f"{float(r['avg_bidder_cnt'] or 0):>7.0f}"
            )

    # ═══════════════════════════════════════════
    # 5. 참여자 수 분포
    # ═══════════════════════════════════════════

    def _analyze_bidder_count_dist(self) -> dict:
        sql = f"""
            SELECT
                CASE
                    WHEN bidder_cnt <= 5 THEN '1~5'
                    WHEN bidder_cnt <= 10 THEN '6~10'
                    WHEN bidder_cnt <= 20 THEN '11~20'
                    WHEN bidder_cnt <= 50 THEN '21~50'
                    WHEN bidder_cnt <= 100 THEN '51~100'
                    WHEN bidder_cnt <= 200 THEN '101~200'
                    WHEN bidder_cnt <= 500 THEN '201~500'
                    ELSE '500+'
                END AS grp,
                COUNT(DISTINCT (bid_ntce_no, bid_ntce_ord)) AS announcement_cnt,
                AVG(bidder_cnt) AS avg_cnt,
                MIN(bidder_cnt) AS min_cnt,
                MAX(bidder_cnt) AS max_cnt
            FROM g2b_bidresult
            WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
              AND estimated_price > 0 AND bidder_cnt > 0
            GROUP BY grp
            ORDER BY MIN(bidder_cnt)
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, r)) for r in cursor.fetchall()]

    def _print_bidder_count_dist(self, data: list):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 5: 공고당 참여자 수 분포")
        self.stdout.write("=" * 60)
        total = sum(r["announcement_cnt"] for r in data)
        for r in data:
            pct = r["announcement_cnt"] / total * 100
            bar = "▓" * int(pct / 2)
            self.stdout.write(
                f"  {r['grp']:>8s}명: {r['announcement_cnt']:>7,}건 ({pct:>5.1f}%)  "
                f"평균 {float(r['avg_cnt']):>6.0f}명  {bar}"
            )

    # ═══════════════════════════════════════════
    # 6. 가격대 세분화
    # ═══════════════════════════════════════════

    def _analyze_price_segment(self) -> dict:
        sql = f"""
            WITH ranked AS (
                SELECT
                    CASE
                        WHEN presume_price < 1 * {UNIT_EOUK} THEN '0~1억'
                        WHEN presume_price < 2 * {UNIT_EOUK} THEN '1~2억'
                        WHEN presume_price < 3 * {UNIT_EOUK} THEN '2~3억'
                        WHEN presume_price < 5 * {UNIT_EOUK} THEN '3~5억'
                        WHEN presume_price < 10 * {UNIT_EOUK} THEN '5~10억'
                        WHEN presume_price < 30 * {UNIT_EOUK} THEN '10~30억'
                        WHEN presume_price < 50 * {UNIT_EOUK} THEN '30~50억'
                        ELSE '50~100억'
                    END AS segment,
                    bid_amt::float / estimated_price * 100 AS ratio,
                    openg_rank,
                    bidder_cnt
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND bid_amt::float / estimated_price * 100 BETWEEN 70 AND 110
            )
            SELECT
                segment,
                COUNT(*) AS total_bids,
                COUNT(DISTINCT CASE WHEN openg_rank = '1' THEN 1 END) AS dummy,
                SUM(CASE WHEN openg_rank = '1' THEN 1 ELSE 0 END) AS rank1_cnt,
                AVG(CASE WHEN openg_rank = '1' THEN ratio END) AS rank1_avg,
                STDDEV_POP(CASE WHEN openg_rank = '1' THEN ratio END) AS rank1_std,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY CASE WHEN openg_rank = '1' THEN ratio END) AS rank1_p50,
                AVG(ratio) AS total_avg,
                AVG(bidder_cnt) AS avg_bidders
            FROM ranked
            GROUP BY segment
            ORDER BY MIN(presume_price)
        """
        # segment 정렬을 위해 MIN(presume_price)는 서브쿼리에 없으므로 다시
        sql_fixed = f"""
            SELECT
                segment,
                total_bids, rank1_cnt, rank1_avg, rank1_std, rank1_p50,
                total_avg, avg_bidders
            FROM (
                SELECT
                    CASE
                        WHEN presume_price < {1 * UNIT_EOUK}::bigint THEN '0~1억'
                        WHEN presume_price < {2 * UNIT_EOUK}::bigint THEN '1~2억'
                        WHEN presume_price < {3 * UNIT_EOUK}::bigint THEN '2~3억'
                        WHEN presume_price < {5 * UNIT_EOUK}::bigint THEN '3~5억'
                        WHEN presume_price < {10 * UNIT_EOUK}::bigint THEN '5~10억'
                        WHEN presume_price < {30 * UNIT_EOUK}::bigint THEN '10~30억'
                        WHEN presume_price < {50 * UNIT_EOUK}::bigint THEN '30~50억'
                        ELSE '50~100억'
                    END AS segment,
                    MIN(presume_price) AS seg_order,
                    COUNT(*) AS total_bids,
                    SUM(CASE WHEN openg_rank = '1' THEN 1 ELSE 0 END) AS rank1_cnt,
                    AVG(CASE WHEN openg_rank = '1' THEN bid_amt::float / estimated_price * 100 END) AS rank1_avg,
                    STDDEV_POP(CASE WHEN openg_rank = '1' THEN bid_amt::float / estimated_price * 100 END) AS rank1_std,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (
                        ORDER BY CASE WHEN openg_rank = '1' THEN bid_amt::float / estimated_price * 100 END
                    ) AS rank1_p50,
                    AVG(bid_amt::float / estimated_price * 100) AS total_avg,
                    AVG(bidder_cnt) AS avg_bidders
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}::bigint
                  AND estimated_price > 0 AND bid_amt > 0
                  AND bid_amt::float / estimated_price * 100 BETWEEN 70 AND 110
                GROUP BY segment
            ) t
            ORDER BY seg_order
        """
        with connection.cursor() as cursor:
            cursor.execute(sql_fixed)
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, r)) for r in cursor.fetchall()]

    def _print_price_segment(self, data: list):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 6: 가격대별 낙찰자 투찰비율")
        self.stdout.write("=" * 60)
        self.stdout.write(
            f"  {'가격대':>10s}  {'낙찰자수':>8s}  {'평균':>7s}  "
            f"{'σ':>6s}  {'P50':>7s}  {'평균참여':>7s}"
        )
        self.stdout.write("  " + "-" * 55)
        for r in data:
            self.stdout.write(
                f"  {r['segment']:>10s}  {r['rank1_cnt']:>8,}  "
                f"{float(r['rank1_avg'] or 0):>7.2f}%  "
                f"{float(r['rank1_std'] or 0):>6.2f}  "
                f"{float(r['rank1_p50'] or 0):>7.2f}%  "
                f"{float(r['avg_bidders'] or 0):>7.0f}명"
            )

    # ═══════════════════════════════════════════
    # 7. 낙찰하한율 근처 탈락
    # ═══════════════════════════════════════════

    def _analyze_threshold_risk(self) -> dict:
        # 하한율 기준 (제도 변경 전)
        sql = f"""
            WITH bid_data AS (
                SELECT
                    bid_amt::float / estimated_price * 100 AS ratio,
                    openg_rank,
                    CASE
                        WHEN presume_price < 1 * {UNIT_EOUK} THEN 87.745
                        WHEN presume_price < 5 * {UNIT_EOUK} THEN 86.745
                        WHEN presume_price < 10 * {UNIT_EOUK} THEN 85.495
                        ELSE 79.995
                    END AS threshold_pre,
                    CASE
                        WHEN presume_price < 1 * {UNIT_EOUK} THEN 89.745
                        WHEN presume_price < 5 * {UNIT_EOUK} THEN 88.745
                        WHEN presume_price < 10 * {UNIT_EOUK} THEN 87.495
                        ELSE 81.995
                    END AS threshold_post,
                    CASE
                        WHEN presume_price < 1 * {UNIT_EOUK} THEN '<1억'
                        WHEN presume_price < 5 * {UNIT_EOUK} THEN '1~5억'
                        WHEN presume_price < 10 * {UNIT_EOUK} THEN '5~10억'
                        ELSE '10~100억'
                    END AS price_group
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND bid_amt::float / estimated_price * 100 BETWEEN 70 AND 110
            )
            SELECT
                price_group,
                threshold_pre,
                threshold_post,
                COUNT(*) AS total,
                SUM(CASE WHEN ratio < threshold_pre THEN 1 ELSE 0 END) AS below_pre,
                SUM(CASE WHEN ratio >= threshold_pre AND ratio < threshold_post THEN 1 ELSE 0 END) AS between_pre_post,
                SUM(CASE WHEN ratio >= threshold_pre AND ratio < threshold_pre + 0.5 THEN 1 ELSE 0 END) AS near_threshold_pre,
                SUM(CASE WHEN ratio >= threshold_post AND ratio < threshold_post + 0.5 THEN 1 ELSE 0 END) AS near_threshold_post
            FROM bid_data
            GROUP BY price_group, threshold_pre, threshold_post
            ORDER BY threshold_pre
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, r)) for r in cursor.fetchall()]

    def _print_threshold_risk(self, data: list):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 7: 낙찰하한율 근처 탈락 분석")
        self.stdout.write("  * 제도 변경 전 하한율 기준. bid/est 단순 비율.")
        self.stdout.write("=" * 60)
        for r in data:
            total = r["total"]
            below = r["below_pre"]
            between = r["between_pre_post"]
            self.stdout.write(
                f"\n  [{r['price_group']}] "
                f"하한율(전): {float(r['threshold_pre']):.3f}%  "
                f"하한율(후): {float(r['threshold_post']):.3f}%"
            )
            self.stdout.write(f"    전체: {total:,}건")
            self.stdout.write(
                f"    하한율(전) 미만 탈락: {below:,}건 ({below/total*100:.1f}%)"
            )
            self.stdout.write(
                f"    전↔후 사이 (새로 탈락 위험): {between:,}건 ({between/total*100:.1f}%)"
            )
            self.stdout.write(
                f"    하한율(전)+0.5%p 이내: {r['near_threshold_pre']:,}건 "
                f"({r['near_threshold_pre']/total*100:.1f}%)"
            )

    # ═══════════════════════════════════════════
    # 8. 기준율 90% 근처 밀집도
    # ═══════════════════════════════════════════

    def _analyze_base_rate_density(self) -> dict:
        sql = f"""
            WITH bid_data AS (
                SELECT
                    bid_amt::float / estimated_price * 100 AS ratio,
                    CASE WHEN openg_rank = '1' THEN true ELSE false END AS is_rank1
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND bid_amt::float / estimated_price * 100 BETWEEN 85 AND 95
            )
            SELECT
                is_rank1,
                COUNT(*) AS total,
                SUM(CASE WHEN ABS(ratio - 90.0) < 0.1 THEN 1 ELSE 0 END) AS within_01,
                SUM(CASE WHEN ABS(ratio - 90.0) < 0.2 THEN 1 ELSE 0 END) AS within_02,
                SUM(CASE WHEN ABS(ratio - 90.0) < 0.5 THEN 1 ELSE 0 END) AS within_05,
                SUM(CASE WHEN ABS(ratio - 90.0) < 1.0 THEN 1 ELSE 0 END) AS within_10,
                SUM(CASE WHEN ABS(ratio - 90.0) < 2.0 THEN 1 ELSE 0 END) AS within_20
            FROM bid_data
            GROUP BY is_rank1
        """
        # 0.01% 단위 히스토그램 (89.5~90.5%)
        hist_sql = f"""
            WITH bid_data AS (
                SELECT
                    bid_amt::float / estimated_price * 100 AS ratio,
                    CASE WHEN openg_rank = '1' THEN true ELSE false END AS is_rank1
                FROM g2b_bidresult
                WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0 AND bid_amt > 0
                  AND bid_amt::float / estimated_price * 100 BETWEEN 89.5 AND 90.5
            )
            SELECT
                is_rank1,
                FLOOR(ratio / 0.05) * 0.05 AS bin_lo,
                COUNT(*) AS cnt
            FROM bid_data
            GROUP BY is_rank1, bin_lo
            ORDER BY is_rank1, bin_lo
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c[0] for c in cursor.description]
            density = [dict(zip(cols, r)) for r in cursor.fetchall()]

            cursor.execute(hist_sql)
            hist = [
                {"is_rank1": r[0], "lo": round(float(r[1]), 2), "cnt": r[2]}
                for r in cursor.fetchall()
            ]

        return {"density": density, "histogram": hist}

    def _print_base_rate_density(self, data: dict):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 8: 기준율 90% 근처 밀집도")
        self.stdout.write("=" * 60)
        for d in data["density"]:
            label = "낙찰자" if d["is_rank1"] else "전체"
            total = d["total"]
            self.stdout.write(f"\n  [{label}] 전체 {total:,}건")
            self.stdout.write(f"    90% ± 0.1%p: {d['within_01']:,}건 ({d['within_01']/total*100:.1f}%)")
            self.stdout.write(f"    90% ± 0.2%p: {d['within_02']:,}건 ({d['within_02']/total*100:.1f}%)")
            self.stdout.write(f"    90% ± 0.5%p: {d['within_05']:,}건 ({d['within_05']/total*100:.1f}%)")
            self.stdout.write(f"    90% ± 1.0%p: {d['within_10']:,}건 ({d['within_10']/total*100:.1f}%)")
            self.stdout.write(f"    90% ± 2.0%p: {d['within_20']:,}건 ({d['within_20']/total*100:.1f}%)")

        # 낙찰자 히스토그램
        rank1_hist = [h for h in data["histogram"] if h["is_rank1"]]
        if rank1_hist:
            max_c = max(h["cnt"] for h in rank1_hist)
            self.stdout.write(f"\n  [낙찰자 89.5~90.5% 히스토그램 (0.05%p 단위)]")
            for h in rank1_hist:
                bar = "▓" * int(h["cnt"] / max_c * 30)
                self.stdout.write(
                    f"    {h['lo']:6.2f}~{h['lo']+0.05:<6.2f}: {h['cnt']:>7,}건  {bar}"
                )

    # ═══════════════════════════════════════════
    # JSON 저장
    # ═══════════════════════════════════════════

    def _save_json(self, results: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "meta": {
                "command": "analyze_bid_advanced",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "description": "추가 EDA: 투찰 전략 + 시장 구조 + 제품 직결 분석",
            },
            **results,
        }
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        self.stdout.write(f"\nJSON 저장: {path}")
