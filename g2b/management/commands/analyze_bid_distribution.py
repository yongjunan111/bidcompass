"""예정가격 분포 EDA + 제도 변경 전후 비교.

32M BidResult 데이터로 예정가격/기초금액 비율, 투찰비율 분포를 분석하고
2026.01.30 낙찰하한율 +2%p 제도 변경 전후를 비교한다.

이 EDA의 output(별표별 예가 분포 + 낙찰자 투찰 집중 구간)은
Phase 2 시나리오 분석에서 1,365가지 예정가격 조합의 확률 가중치 입력으로 사용된다.

사용:
    python manage.py analyze_bid_distribution
    python manage.py analyze_bid_distribution --limit 1000
    python manage.py analyze_bid_distribution --output data/collected/bid_distribution_eda.json
"""

import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UNIT_EOUK = 1_0000_0000

# 별표 경계 (원) — [하한, 상한)
TABLE_BOUNDARIES = [
    ("TABLE_5", 0, 2 * UNIT_EOUK),
    ("TABLE_4", 2 * UNIT_EOUK, 3 * UNIT_EOUK),
    ("TABLE_3", 3 * UNIT_EOUK, 10 * UNIT_EOUK),
    ("TABLE_2A", 10 * UNIT_EOUK, 50 * UNIT_EOUK),
    ("TABLE_1", 50 * UNIT_EOUK, 100 * UNIT_EOUK),
]

REGULATION_DATE = "20260130"
MIN_TABLE_N = 50


def make_bar(count: int, max_count: int, width: int = 30) -> str:
    if max_count == 0:
        return ""
    w = int(count / max_count * width)
    return "\u2593" * w


def percentile(sorted_vals: list[float], p: float) -> float:
    """p는 0~100."""
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p / 100
    f = int(k)
    c = f + 1
    if c >= len(sorted_vals):
        return sorted_vals[-1]
    return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])


class Command(BaseCommand):
    help = "예정가격 분포 EDA + 제도 변경 전후 비교"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=0,
            help="공고 수 제한 (디버깅용, 0=전체)",
        )
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        output_path = options["output"]

        self.stdout.write("=" * 60)
        self.stdout.write("  예정가격 분포 EDA + 제도 변경 전후 비교")
        self.stdout.write("=" * 60)

        # 1. 공고 레벨 데이터 (예가/기초 비율)
        self.stdout.write("\n[1] 공고 레벨 데이터 집계 중...")
        announcement_data = self._query_announcement_level(limit)
        self.stdout.write(f"  총 {len(announcement_data)}건 조회")

        # 2. 분석 1: 예가/기초 비율
        result_1 = self._analyze_est_base_ratio(announcement_data)
        self._print_est_base_ratio(result_1)

        # 3. 분석 2: 투찰비율 (SQL 집계 — 메모리 절약)
        self.stdout.write("\n[2] 투찰 비율 SQL 집계 중...")
        bid_stats = self._query_bid_ratio_stats(limit)
        self.stdout.write(f"  {len(bid_stats)}개 그룹 집계 완료")
        bid_hist = self._query_bid_ratio_histogram(limit)
        self.stdout.write(f"  히스토그램 {len(bid_hist)}개 빈 집계 완료")
        result_2 = self._analyze_bid_ratio(bid_stats, bid_hist)
        self._print_bid_ratio(result_2)

        # 4. 분석 3: 참여업체 수별
        result_3 = self._analyze_by_bidder_count(announcement_data)
        self._print_by_bidder_count(result_3)

        # 5. 분석 4: 제도 변경 전후 종합 비교
        result_4 = self._build_comparison(result_1, result_2)
        self._print_comparison(result_4)

        # 6. JSON 저장
        if output_path:
            self._save_json(
                {"est_base_ratio": result_1, "bid_ratio": result_2,
                 "by_bidder_count": result_3, "comparison": result_4},
                output_path,
            )

    # ──────────────────────────────────────────
    # SQL 쿼리
    # ──────────────────────────────────────────

    def _query_announcement_level(self, limit: int) -> list[dict]:
        """공고 레벨: 예가/기초 비율 + 별표 구간 + 제도 전후."""
        limit_clause = f"LIMIT {limit}" if limit > 0 else ""
        sql = f"""
            SELECT
                r.bid_ntce_no,
                r.bid_ntce_ord,
                r.estimated_price,
                r.base_amt,
                r.presume_price,
                r.bidder_cnt,
                c.openg_date
            FROM (
                SELECT DISTINCT ON (bid_ntce_no, bid_ntce_ord)
                    bid_ntce_no, bid_ntce_ord,
                    estimated_price, base_amt, presume_price, bidder_cnt
                FROM g2b_bidresult
                WHERE presume_price > 0
                  AND presume_price < {100 * UNIT_EOUK}
                  AND estimated_price > 0
                  AND base_amt > 0
                ORDER BY bid_ntce_no, bid_ntce_ord
            ) r
            LEFT JOIN (
                SELECT DISTINCT ON (bid_ntce_no, bid_ntce_ord)
                    bid_ntce_no, bid_ntce_ord, openg_date
                FROM g2b_bidcontract
                WHERE openg_date != ''
                ORDER BY bid_ntce_no, bid_ntce_ord
            ) c ON r.bid_ntce_no = c.bid_ntce_no
                AND r.bid_ntce_ord = c.bid_ntce_ord
            {limit_clause}
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [col[0] for col in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _query_bid_ratio_stats(self, limit: int) -> list[dict]:
        """투찰비율 통계를 SQL 집계로 반환 (메모리 절약)."""
        # limit 적용: 공고 수 기준으로 필터
        limit_filter = ""
        if limit > 0:
            limit_filter = f"""
                AND (r.bid_ntce_no, r.bid_ntce_ord) IN (
                    SELECT DISTINCT bid_ntce_no, bid_ntce_ord
                    FROM g2b_bidresult
                    WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                      AND estimated_price > 0 AND bid_amt > 0
                    LIMIT {limit}
                )
            """
        sql = f"""
            WITH bid_data AS (
                SELECT
                    r.bid_amt::float / r.estimated_price * 100 AS ratio,
                    CASE WHEN r.openg_rank = '1' THEN true ELSE false END AS is_rank1,
                    CASE
                        WHEN r.presume_price < {2 * UNIT_EOUK} THEN 'TABLE_5'
                        WHEN r.presume_price < {3 * UNIT_EOUK} THEN 'TABLE_4'
                        WHEN r.presume_price < {10 * UNIT_EOUK} THEN 'TABLE_3'
                        WHEN r.presume_price < {50 * UNIT_EOUK} THEN 'TABLE_2A'
                        ELSE 'TABLE_1'
                    END AS table_seg,
                    CASE
                        WHEN c.openg_date IS NULL OR c.openg_date = '' THEN 'unknown'
                        WHEN c.openg_date >= '{REGULATION_DATE}' THEN 'post'
                        ELSE 'pre'
                    END AS period
                FROM g2b_bidresult r
                LEFT JOIN (
                    SELECT DISTINCT ON (bid_ntce_no, bid_ntce_ord)
                        bid_ntce_no, bid_ntce_ord, openg_date
                    FROM g2b_bidcontract
                    WHERE openg_date != ''
                    ORDER BY bid_ntce_no, bid_ntce_ord
                ) c ON r.bid_ntce_no = c.bid_ntce_no
                    AND r.bid_ntce_ord = c.bid_ntce_ord
                WHERE r.presume_price > 0
                  AND r.presume_price < {100 * UNIT_EOUK}
                  AND r.estimated_price > 0
                  AND r.bid_amt > 0
                  {limit_filter}
            )
            SELECT
                is_rank1, table_seg, period,
                COUNT(*) AS n,
                AVG(ratio) AS mean,
                STDDEV_POP(ratio) AS std,
                MIN(ratio) AS min_val,
                MAX(ratio) AS max_val,
                PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY ratio) AS p5,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratio) AS p25,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ratio) AS p50,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratio) AS p75,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ratio) AS p95,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ratio) AS p99
            FROM bid_data
            WHERE ratio BETWEEN 70 AND 110
            GROUP BY is_rank1, table_seg, period
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [col[0] for col in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _query_bid_ratio_histogram(self, limit: int) -> list[dict]:
        """투찰비율 히스토그램을 SQL로 반환."""
        limit_filter = ""
        if limit > 0:
            limit_filter = f"""
                AND (r.bid_ntce_no, r.bid_ntce_ord) IN (
                    SELECT DISTINCT bid_ntce_no, bid_ntce_ord
                    FROM g2b_bidresult
                    WHERE presume_price > 0 AND presume_price < {100 * UNIT_EOUK}
                      AND estimated_price > 0 AND bid_amt > 0
                    LIMIT {limit}
                )
            """
        sql = f"""
            WITH bid_data AS (
                SELECT
                    r.bid_amt::float / r.estimated_price * 100 AS ratio,
                    CASE WHEN r.openg_rank = '1' THEN true ELSE false END AS is_rank1
                FROM g2b_bidresult r
                WHERE r.presume_price > 0
                  AND r.presume_price < {100 * UNIT_EOUK}
                  AND r.estimated_price > 0
                  AND r.bid_amt > 0
                  {limit_filter}
            )
            SELECT
                is_rank1,
                FLOOR(ratio / 0.2) * 0.2 AS bin_lo,
                COUNT(*) AS cnt
            FROM bid_data
            WHERE ratio >= 85 AND ratio < 95
            GROUP BY is_rank1, bin_lo
            ORDER BY is_rank1, bin_lo
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [col[0] for col in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    # ──────────────────────────────────────────
    # 분석 1: 예가/기초 비율
    # ──────────────────────────────────────────

    def _classify_table(self, presume_price: int) -> str:
        for name, lo, hi in TABLE_BOUNDARIES:
            if lo <= presume_price < hi:
                return name
        return "UNKNOWN"

    def _classify_period(self, openg_date: str | None) -> str:
        if not openg_date:
            return "unknown"
        return "post" if openg_date >= REGULATION_DATE else "pre"

    def _calc_stats(self, values: list[float]) -> dict:
        if not values:
            return {"n": 0}
        s = sorted(values)
        n = len(s)
        mean = sum(s) / n
        var = sum((x - mean) ** 2 for x in s) / n
        std = var ** 0.5
        return {
            "n": n,
            "mean": round(mean, 4),
            "std": round(std, 4),
            "min": round(s[0], 4),
            "p5": round(percentile(s, 5), 4),
            "p25": round(percentile(s, 25), 4),
            "p50": round(percentile(s, 50), 4),
            "p75": round(percentile(s, 75), 4),
            "p95": round(percentile(s, 95), 4),
            "p99": round(percentile(s, 99), 4),
            "max": round(s[-1], 4),
        }

    def _make_histogram(
        self, values: list[float], lo: float, hi: float, bin_width: float,
    ) -> list[dict]:
        bins = []
        edge = lo
        while edge < hi - bin_width / 2:
            upper = edge + bin_width
            count = sum(1 for v in values if edge <= v < upper)
            bins.append({
                "lo": round(edge, 2),
                "hi": round(upper, 2),
                "count": count,
            })
            edge = upper
        return bins

    def _analyze_est_base_ratio(self, data: list[dict]) -> dict:
        # ratio = estimated_price / base_amt * 100
        result = {"all": {}, "by_table": {}, "pre": {}, "post": {}}
        result["by_table_pre"] = {}
        result["by_table_post"] = {}

        all_ratios = []
        by_table: dict[str, list[float]] = {}
        by_period: dict[str, list[float]] = {"pre": [], "post": []}
        by_table_period: dict[str, dict[str, list[float]]] = {}

        for row in data:
            ratio = row["estimated_price"] / row["base_amt"] * 100
            if ratio < 97 or ratio > 103:
                continue

            table = self._classify_table(row["presume_price"])
            period = self._classify_period(row.get("openg_date"))

            all_ratios.append(ratio)

            by_table.setdefault(table, []).append(ratio)

            if period in ("pre", "post"):
                by_period[period].append(ratio)
                by_table_period.setdefault(table, {}).setdefault(period, []).append(ratio)

        result["all"] = self._calc_stats(all_ratios)
        result["all"]["histogram"] = self._make_histogram(all_ratios, 97, 103, 0.1)

        for table, vals in sorted(by_table.items()):
            result["by_table"][table] = self._calc_stats(vals)

        for period in ("pre", "post"):
            result[period] = self._calc_stats(by_period[period])
            result[period]["histogram"] = self._make_histogram(
                by_period[period], 97, 103, 0.1,
            )

        for table, periods in sorted(by_table_period.items()):
            for period in ("pre", "post"):
                vals = periods.get(period, [])
                key = f"by_table_{period}"
                result[key][table] = self._calc_stats(vals)

        return result

    # ──────────────────────────────────────────
    # 분석 2: 투찰비율
    # ──────────────────────────────────────────

    def _sql_row_to_stats(self, row: dict) -> dict:
        """SQL 집계 행 → stats dict 변환."""
        n = row["n"]
        if n == 0:
            return {"n": 0}
        return {
            "n": n,
            "mean": round(float(row["mean"]), 4),
            "std": round(float(row["std"] or 0), 4),
            "min": round(float(row["min_val"]), 4),
            "p5": round(float(row["p5"]), 4),
            "p25": round(float(row["p25"]), 4),
            "p50": round(float(row["p50"]), 4),
            "p75": round(float(row["p75"]), 4),
            "p95": round(float(row["p95"]), 4),
            "p99": round(float(row["p99"]), 4),
            "max": round(float(row["max_val"]), 4),
        }

    def _merge_sql_stats(self, rows_list: list[dict]) -> dict:
        """여러 SQL 집계 행을 하나로 합산 (가중 평균)."""
        total_n = sum(r["n"] for r in rows_list)
        if total_n == 0:
            return {"n": 0}

        # 가중 평균 / 가중 표준편차 / min-max / 가중 백분위수 근사
        w_mean = sum(r["n"] * float(r["mean"]) for r in rows_list) / total_n
        w_var = sum(
            r["n"] * (float(r["std"] or 0) ** 2 + (float(r["mean"]) - w_mean) ** 2)
            for r in rows_list
        ) / total_n
        # 백분위수: 가장 큰 그룹 기준 (정확하진 않지만 근사)
        biggest = max(rows_list, key=lambda r: r["n"])
        return {
            "n": total_n,
            "mean": round(w_mean, 4),
            "std": round(w_var ** 0.5, 4),
            "min": round(min(float(r["min_val"]) for r in rows_list), 4),
            "p5": round(float(biggest["p5"]), 4),
            "p25": round(float(biggest["p25"]), 4),
            "p50": round(float(biggest["p50"]), 4),
            "p75": round(float(biggest["p75"]), 4),
            "p95": round(float(biggest["p95"]), 4),
            "p99": round(float(biggest["p99"]), 4),
            "max": round(max(float(r["max_val"]) for r in rows_list), 4),
        }

    def _analyze_bid_ratio(self, stats_rows: list[dict], hist_rows: list[dict]) -> dict:
        result = {
            "rank1_all": {}, "rank1_pre": {}, "rank1_post": {},
            "total_all": {}, "total_pre": {}, "total_post": {},
            "rank1_by_table": {}, "total_by_table": {},
        }

        # 그룹별 분류
        grouped: dict[tuple, list[dict]] = {}
        for row in stats_rows:
            key = (row["is_rank1"], row["table_seg"], row["period"])
            grouped.setdefault(key, []).append(row)

        def collect(is_rank1: bool, table: str | None, period: str | None) -> list[dict]:
            """조건에 맞는 행들을 수집."""
            matches = []
            for (r, t, p), rows in grouped.items():
                if r != is_rank1:
                    continue
                if table is not None and t != table:
                    continue
                if period is not None and p != period:
                    continue
                matches.extend(rows)
            return matches

        # rank1
        for prefix, is_rank1 in [("rank1", True), ("total", False)]:
            # all
            all_rows = collect(is_rank1, None, None)
            if all_rows:
                result[f"{prefix}_all"] = self._merge_sql_stats(all_rows)
            # pre/post
            for period in ("pre", "post"):
                p_rows = collect(is_rank1, None, period)
                if p_rows:
                    result[f"{prefix}_{period}"] = self._merge_sql_stats(p_rows)
            # by_table
            for table in ["TABLE_5", "TABLE_4", "TABLE_3", "TABLE_2A", "TABLE_1"]:
                t_rows = collect(is_rank1, table, None)
                if t_rows:
                    result[f"{prefix}_by_table"][table] = self._merge_sql_stats(t_rows)

        # 히스토그램
        for prefix, is_rank1 in [("rank1", True), ("total", False)]:
            bins = {}
            for row in hist_rows:
                if row["is_rank1"] != is_rank1:
                    continue
                lo = round(float(row["bin_lo"]), 1)
                bins[lo] = bins.get(lo, 0) + row["cnt"]
            histogram = []
            edge = 85.0
            while edge < 94.9:
                histogram.append({
                    "lo": round(edge, 1),
                    "hi": round(edge + 0.2, 1),
                    "count": bins.get(round(edge, 1), 0),
                })
                edge += 0.2
            if f"{prefix}_all" in result:
                result[f"{prefix}_all"]["histogram"] = histogram

        return result

    # ──────────────────────────────────────────
    # 분석 3: 참여업체 수별
    # ──────────────────────────────────────────

    def _analyze_by_bidder_count(self, data: list[dict]) -> dict:
        groups = [
            ("~10", 0, 11),
            ("11~50", 11, 51),
            ("51~100", 51, 101),
            ("100+", 101, 999999),
        ]
        result = {}
        for label, lo, hi in groups:
            ratios = []
            for row in data:
                cnt = row.get("bidder_cnt") or 0
                if not (lo <= cnt < hi):
                    continue
                ratio = row["estimated_price"] / row["base_amt"] * 100
                if 97 <= ratio <= 103:
                    ratios.append(ratio)
            result[label] = self._calc_stats(ratios)
        return result

    # ──────────────────────────────────────────
    # 분석 4: 전후 비교 테이블
    # ──────────────────────────────────────────

    def _build_comparison(self, r1: dict, r2: dict) -> dict:
        rows = []
        for label, pre_key, post_key in [
            ("예가/기초 비율", "pre", "post"),
            ("낙찰자 투찰비율", "rank1_pre", "rank1_post"),
            ("전체 투찰비율", "total_pre", "total_post"),
        ]:
            pre = r1.get(pre_key) or r2.get(pre_key) or {}
            post = r1.get(post_key) or r2.get(post_key) or {}
            pre_mean = pre.get("mean", 0)
            post_mean = post.get("mean", 0)
            pre_std = pre.get("std", 0)
            post_std = post.get("std", 0)
            rows.append({
                "label": label,
                "pre_n": pre.get("n", 0),
                "post_n": post.get("n", 0),
                "pre_mean": pre_mean,
                "post_mean": post_mean,
                "diff_mean": round(post_mean - pre_mean, 4),
                "pre_std": pre_std,
                "post_std": post_std,
                "diff_std": round(post_std - pre_std, 4),
            })
        return {"rows": rows}

    # ──────────────────────────────────────────
    # 출력
    # ──────────────────────────────────────────

    def _print_stats_line(self, label: str, stats: dict, warn_n: bool = True):
        n = stats.get("n", 0)
        if n == 0:
            self.stdout.write(f"  {label}: (데이터 없음)")
            return
        warn = " [표본 부족]" if warn_n and n < MIN_TABLE_N else ""
        self.stdout.write(
            f"  {label} (N={n:,}{warn}):"
            f"  평균={stats['mean']:.2f}%  σ={stats['std']:.2f}%"
            f"  P50={stats['p50']:.2f}%  P95={stats['p95']:.2f}%"
        )

    def _print_histogram(self, histogram: list[dict]):
        if not histogram:
            return
        max_c = max(b["count"] for b in histogram) if histogram else 1
        for b in histogram:
            lo, hi, count = b["lo"], b["hi"], b["count"]
            bar = make_bar(count, max_c)
            self.stdout.write(
                f"    {lo:6.1f}~{hi:<6.1f}: {count:>7,}건  {bar}"
            )

    def _print_est_base_ratio(self, result: dict):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 1: 예정가격/기초금액 비율 (97~103% 필터)")
        self.stdout.write("=" * 60)

        self._print_stats_line("전체", result["all"], warn_n=False)
        self.stdout.write("\n  히스토그램 (0.1%p 단위):")
        self._print_histogram(result["all"].get("histogram", []))

        self.stdout.write("\n  [별표별]")
        order = ["TABLE_5", "TABLE_4", "TABLE_3", "TABLE_2A", "TABLE_1"]
        labels = {"TABLE_5": "<2억", "TABLE_4": "2~3억", "TABLE_3": "3~10억",
                  "TABLE_2A": "10~50억", "TABLE_1": "50~100억"}
        for t in order:
            stats = result["by_table"].get(t, {"n": 0})
            self._print_stats_line(f"{t} ({labels[t]})", stats)

        self.stdout.write("\n  [제도 변경 전]")
        self._print_stats_line("변경 전", result["pre"], warn_n=False)
        self.stdout.write("  히스토그램:")
        self._print_histogram(result["pre"].get("histogram", []))

        self.stdout.write("\n  [제도 변경 후]")
        self._print_stats_line("변경 후", result["post"], warn_n=False)
        self.stdout.write("  히스토그램:")
        self._print_histogram(result["post"].get("histogram", []))

        self.stdout.write("\n  [별표별 × 제도 전후]")
        for t in order:
            pre_s = result.get("by_table_pre", {}).get(t, {"n": 0})
            post_s = result.get("by_table_post", {}).get(t, {"n": 0})
            self._print_stats_line(f"{t} 전", pre_s)
            self._print_stats_line(f"{t} 후", post_s)

    def _print_bid_ratio(self, result: dict):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 2: 투찰금액/예정가격 비율 (70~110% 필터)")
        self.stdout.write("  * 주의: bid/est 단순 비율이며 코어엔진의")
        self.stdout.write("    ratio (bid-A)/(est-A)와 다릅니다.")
        self.stdout.write("    A값 반영 분석은 API 수집 데이터 확보 후 별도 수행.")
        self.stdout.write("=" * 60)

        self.stdout.write("\n  [1순위(낙찰자)]")
        self._print_stats_line("전체", result["rank1_all"], warn_n=False)
        self.stdout.write("  히스토그램 (85~95%, 0.2%p 단위):")
        self._print_histogram(result["rank1_all"].get("histogram", []))

        self.stdout.write("\n  [전체 입찰자]")
        self._print_stats_line("전체", result["total_all"], warn_n=False)

        self.stdout.write("\n  [1순위 별표별]")
        order = ["TABLE_5", "TABLE_4", "TABLE_3", "TABLE_2A", "TABLE_1"]
        for t in order:
            stats = result["rank1_by_table"].get(t, {"n": 0})
            self._print_stats_line(t, stats)

        self.stdout.write("\n  [1순위 제도 전후]")
        self._print_stats_line("변경 전", result["rank1_pre"], warn_n=False)
        self._print_stats_line("변경 후", result["rank1_post"], warn_n=False)

    def _print_by_bidder_count(self, result: dict):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 3: 참여업체 수별 예가/기초 비율")
        self.stdout.write("=" * 60)
        for label in ["~10", "11~50", "51~100", "100+"]:
            stats = result.get(label, {"n": 0})
            self._print_stats_line(label, stats)

    def _print_comparison(self, result: dict):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  분석 4: 제도 변경 전후 종합 비교")
        self.stdout.write("=" * 60)
        self.stdout.write(
            f"  {'지표':<20s} {'전 N':>8s} {'후 N':>8s}"
            f" {'전 평균':>8s} {'후 평균':>8s} {'차이':>8s}"
            f" {'전 σ':>7s} {'후 σ':>7s}"
        )
        self.stdout.write("  " + "-" * 85)
        for row in result["rows"]:
            self.stdout.write(
                f"  {row['label']:<20s}"
                f" {row['pre_n']:>8,} {row['post_n']:>8,}"
                f" {row['pre_mean']:>8.2f} {row['post_mean']:>8.2f}"
                f" {row['diff_mean']:>+8.4f}"
                f" {row['pre_std']:>7.2f} {row['post_std']:>7.2f}"
            )

    # ──────────────────────────────────────────
    # JSON 저장
    # ──────────────────────────────────────────

    def _save_json(self, results: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "meta": {
                "command": "analyze_bid_distribution",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "description": "예정가격 분포 EDA + 제도 변경 전후 비교",
                "regulation_date": REGULATION_DATE,
                "ratio_filter": "97~103% (est/base), 70~110% (bid/est)",
            },
            **results,
        }

        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        self.stdout.write(f"\nJSON 저장: {path}")
