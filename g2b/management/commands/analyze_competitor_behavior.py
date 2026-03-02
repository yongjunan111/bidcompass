"""BC-34: Phase 2 심층 EDA — 경쟁자 행동 분석.

기존 EDA(1D GROUP BY)와 달리 다차원 교차분석 + 통계 검정 + 행동 분류.
32M건 BidResult를 공통 임시테이블 1회 생성 후 6개 분석이 재사용.

분석 목록:
  1. 세그먼트별 투찰비율 분포 (2D GROUP BY + percentile)
  2. 투찰비율 히스토그램 (0.1%p bin, 86~94%)
  3. 다빈도 업체 프로파일링 (행동 아키타입 분류)
  4. 입찰자수 × 낙찰비율 교차분석
  5. 분포 형태 (skewness/kurtosis)
  6. 월별 경쟁 강도 추이

⚠️ M1 8GB: 모든 분석 SQL 집계, Python에는 수십~수백 행만 반환.

사용:
    python manage.py analyze_competitor_behavior
    python manage.py analyze_competitor_behavior --output data/collected/competitor_behavior_eda.json
"""

import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UNIT_EOUK = 1_0000_0000

# 가격대 세그먼트 (별표 라우팅과 동일 경계값)
SEGMENTS = [
    ("2억 미만", 0, 2 * UNIT_EOUK),
    ("2~3억", 2 * UNIT_EOUK, 3 * UNIT_EOUK),
    ("3~10억", 3 * UNIT_EOUK, 10 * UNIT_EOUK),
    ("10~50억", 10 * UNIT_EOUK, 50 * UNIT_EOUK),
    ("50~100억", 50 * UNIT_EOUK, 100 * UNIT_EOUK),
]


class Command(BaseCommand):
    help = "BC-34: Phase 2 심층 EDA — 경쟁자 행동 분석"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로",
        )

    def handle(self, *args, **options):
        output_path = options["output"]
        results = {}

        self.stdout.write("=" * 60)
        self.stdout.write("  BC-34: 경쟁자 행동 분석 (Phase 2 심층 EDA)")
        self.stdout.write("=" * 60)

        # 0. 공통 임시테이블 생성 (32M → 적격심사 대상만 필터)
        self.stdout.write("\n[0] 공통 임시테이블 생성 중...")
        base_count = self._create_base_table()
        self.stdout.write(f"  _eda_base: {base_count:,}건")
        results["base_count"] = base_count

        # 1. 세그먼트별 투찰비율 분포
        self.stdout.write("\n[1] 세그먼트별 투찰비율 분포...")
        results["segment_distribution"] = self._analyze_segment_distribution()
        self._print_segment_distribution(results["segment_distribution"])

        # 2. 투찰비율 히스토그램
        self.stdout.write("\n[2] 투찰비율 히스토그램 (0.1%p bin)...")
        results["ratio_histogram"] = self._analyze_ratio_histogram()
        self._print_ratio_histogram(results["ratio_histogram"])

        # 3. 다빈도 업체 프로파일링
        self.stdout.write("\n[3] 다빈도 업체 프로파일링...")
        results["company_profiles"] = self._analyze_company_profiles()
        self._print_company_profiles(results["company_profiles"])

        # 4. 입찰자수 × 낙찰비율 교차분석
        self.stdout.write("\n[4] 입찰자수 × 낙찰비율 교차분석...")
        results["bidder_count_cross"] = self._analyze_bidder_count_cross()
        self._print_bidder_count_cross(results["bidder_count_cross"])

        # 5. 분포 형태 (skewness/kurtosis)
        self.stdout.write("\n[5] 분포 형태 (skewness/kurtosis)...")
        results["distribution_shape"] = self._analyze_distribution_shape()
        self._print_distribution_shape(results["distribution_shape"])

        # 6. 월별 경쟁 강도 추이
        self.stdout.write("\n[6] 월별 경쟁 강도 추이...")
        results["monthly_competition"] = self._analyze_monthly_competition()
        self._print_monthly_competition(results["monthly_competition"])

        # 임시테이블 정리
        self._drop_base_table()

        # JSON 저장
        if output_path:
            self._save_json(results, output_path)

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("  BC-34 경쟁자 행동 분석 완료"))
        self.stdout.write("=" * 60)

    # ──────────────────────────────────────────
    # 0. 공통 임시테이블
    # ──────────────────────────────────────────

    def _create_base_table(self) -> int:
        """적격심사 대상 필터링된 임시테이블 생성. 1회 풀스캔."""
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS _eda_base")
            cursor.execute("""
                CREATE TEMP TABLE _eda_base AS
                SELECT
                    bid_ntce_no, bid_ntce_ord, company_bizno, company_nm,
                    presume_price, estimated_price, bid_amt, openg_rank,
                    bidder_cnt, success_lowest_rate,
                    bid_amt::float / NULLIF(estimated_price, 0) * 100 AS ratio
                FROM g2b_bidresult
                WHERE presume_price > 0
                  AND presume_price < 10000000000
                  AND estimated_price > 0
                  AND bid_amt > 0
                  AND success_lowest_rate > 0
                  AND bid_amt::float / NULLIF(estimated_price, 0) * 100
                      BETWEEN 70 AND 110
            """)
            cursor.execute(
                "CREATE INDEX ON _eda_base (presume_price)"
            )
            cursor.execute(
                "CREATE INDEX ON _eda_base (company_bizno)"
            )
            cursor.execute(
                "CREATE INDEX ON _eda_base (openg_rank)"
            )
            cursor.execute("SELECT COUNT(*) FROM _eda_base")
            return cursor.fetchone()[0]

    def _drop_base_table(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS _eda_base")

    # ──────────────────────────────────────────
    # 1. 세그먼트별 투찰비율 분포
    # ──────────────────────────────────────────

    def _analyze_segment_distribution(self) -> list[dict]:
        """가격대 세그먼트별 투찰비율 percentile + 기본 통계."""
        sql = """
            SELECT
                CASE
                    WHEN presume_price < 200000000 THEN '2억 미만'
                    WHEN presume_price < 300000000 THEN '2~3억'
                    WHEN presume_price < 1000000000 THEN '3~10억'
                    WHEN presume_price < 5000000000 THEN '10~50억'
                    ELSE '50~100억'
                END AS segment,
                COUNT(*) AS cnt,
                AVG(ratio) AS avg_ratio,
                STDDEV(ratio) AS std_ratio,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratio) AS p25,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ratio) AS p50,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratio) AS p75,
                PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY ratio) AS p10,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY ratio) AS p90
            FROM _eda_base
            GROUP BY segment
            ORDER BY MIN(presume_price)
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c.name for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _print_segment_distribution(self, data: list[dict]):
        self.stdout.write(
            f"  {'세그먼트':<10s} {'건수':>10s} {'평균':>7s} "
            f"{'표준편차':>8s} {'P10':>7s} {'P25':>7s} "
            f"{'P50':>7s} {'P75':>7s} {'P90':>7s}"
        )
        for row in data:
            self.stdout.write(
                f"  {row['segment']:<10s} {row['cnt']:>10,d} "
                f"{row['avg_ratio']:>7.2f} {(row['std_ratio'] or 0):>8.2f} "
                f"{row['p10']:>7.2f} {row['p25']:>7.2f} "
                f"{row['p50']:>7.2f} {row['p75']:>7.2f} "
                f"{row['p90']:>7.2f}"
            )

    # ──────────────────────────────────────────
    # 2. 투찰비율 히스토그램
    # ──────────────────────────────────────────

    def _analyze_ratio_histogram(self) -> list[dict]:
        """0.1%p 단위 bin, 86~94% 구간."""
        sql = """
            SELECT
                FLOOR(ratio * 10) / 10 AS bin_start,
                COUNT(*) AS cnt
            FROM _eda_base
            WHERE ratio BETWEEN 86 AND 94
            GROUP BY bin_start
            ORDER BY bin_start
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return [
                {"bin_start": float(row[0]), "cnt": row[1]}
                for row in cursor.fetchall()
            ]

    def _print_ratio_histogram(self, data: list[dict]):
        if not data:
            self.stdout.write("  (데이터 없음)")
            return
        max_cnt = max(d["cnt"] for d in data)
        for row in data:
            bar_len = int(row["cnt"] / max_cnt * 40) if max_cnt else 0
            bar = "#" * bar_len
            self.stdout.write(
                f"  {row['bin_start']:>5.1f}%: {row['cnt']:>8,d} {bar}"
            )

    # ──────────────────────────────────────────
    # 3. 다빈도 업체 프로파일링
    # ──────────────────────────────────────────

    def _analyze_company_profiles(self) -> dict:
        """다빈도 업체(50건+)의 행동 아키타입 분류."""
        # 업체별 통계 (50건 이상)
        sql = """
            SELECT
                company_bizno,
                MAX(company_nm) AS company_nm,
                COUNT(*) AS bid_count,
                AVG(ratio) AS avg_ratio,
                STDDEV(ratio) AS std_ratio,
                MIN(ratio) AS min_ratio,
                MAX(ratio) AS max_ratio
            FROM _eda_base
            WHERE company_bizno != ''
            GROUP BY company_bizno
            HAVING COUNT(*) >= 50
            ORDER BY COUNT(*) DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c.name for c in cursor.description]
            companies = [dict(zip(cols, row)) for row in cursor.fetchall()]

        # 아키타입 분류
        # 초고정(ultra_fixed): std < 0.3
        # 고정(fixed): 0.3 <= std < 1.0
        # 적응(adaptive): 1.0 <= std < 2.0
        # 분산(dispersed): std >= 2.0
        archetypes = {"ultra_fixed": 0, "fixed": 0, "adaptive": 0, "dispersed": 0}
        top_companies = []

        for c in companies:
            std = c["std_ratio"] or 0
            if std < 0.3:
                archetype = "ultra_fixed"
            elif std < 1.0:
                archetype = "fixed"
            elif std < 2.0:
                archetype = "adaptive"
            else:
                archetype = "dispersed"

            archetypes[archetype] += 1
            c["archetype"] = archetype

            if len(top_companies) < 20:
                top_companies.append(c)

        return {
            "total_companies": len(companies),
            "archetypes": archetypes,
            "top_companies": top_companies,
        }

    def _print_company_profiles(self, data: dict):
        self.stdout.write(f"  50건+ 업체: {data['total_companies']}개")
        self.stdout.write(f"  행동 아키타입 분류:")
        labels = {
            "ultra_fixed": "초고정 (σ<0.3)",
            "fixed": "고정 (0.3≤σ<1.0)",
            "adaptive": "적응 (1.0≤σ<2.0)",
            "dispersed": "분산 (σ≥2.0)",
        }
        total = data["total_companies"] or 1
        for key, label in labels.items():
            cnt = data["archetypes"][key]
            pct = cnt / total * 100
            self.stdout.write(f"    {label}: {cnt:>5d}개 ({pct:.1f}%)")

        self.stdout.write(f"\n  상위 10개 다빈도 업체:")
        self.stdout.write(
            f"  {'업체명':<20s} {'입찰수':>6s} {'평균비율':>8s} "
            f"{'σ':>6s} {'유형':<12s}"
        )
        for c in data["top_companies"][:10]:
            nm = (c["company_nm"] or "")[:18]
            self.stdout.write(
                f"  {nm:<20s} {c['bid_count']:>6d} "
                f"{c['avg_ratio']:>8.2f} {(c['std_ratio'] or 0):>6.2f} "
                f"{c['archetype']:<12s}"
            )

    # ──────────────────────────────────────────
    # 4. 입찰자수 × 낙찰비율 교차분석
    # ──────────────────────────────────────────

    def _analyze_bidder_count_cross(self) -> list[dict]:
        """입찰자수 구간별 1순위 투찰비율 분석."""
        sql = """
            SELECT
                CASE
                    WHEN bidder_cnt < 10 THEN '01~9'
                    WHEN bidder_cnt < 30 THEN '10~29'
                    WHEN bidder_cnt < 50 THEN '30~49'
                    WHEN bidder_cnt < 100 THEN '50~99'
                    WHEN bidder_cnt < 200 THEN '100~199'
                    ELSE '200+'
                END AS bidder_group,
                COUNT(*) AS cnt,
                AVG(ratio) AS avg_ratio,
                STDDEV(ratio) AS std_ratio,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ratio) AS median_ratio,
                AVG(CASE WHEN openg_rank = '1' THEN ratio END) AS rank1_avg_ratio,
                COUNT(CASE WHEN openg_rank = '1' THEN 1 END) AS rank1_cnt
            FROM _eda_base
            GROUP BY bidder_group
            ORDER BY MIN(bidder_cnt)
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c.name for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _print_bidder_count_cross(self, data: list[dict]):
        self.stdout.write(
            f"  {'참여자수':>10s} {'전체건수':>10s} {'전체평균':>8s} "
            f"{'1순위수':>8s} {'1순위평균':>10s}"
        )
        for row in data:
            r1_avg = f"{row['rank1_avg_ratio']:.2f}" if row["rank1_avg_ratio"] else "-"
            self.stdout.write(
                f"  {row['bidder_group']:>10s} {row['cnt']:>10,d} "
                f"{row['avg_ratio']:>8.2f} "
                f"{row['rank1_cnt']:>8d} {r1_avg:>10s}"
            )

    # ──────────────────────────────────────────
    # 5. 분포 형태 (skewness/kurtosis)
    # ──────────────────────────────────────────

    def _analyze_distribution_shape(self) -> list[dict]:
        """세그먼트별 skewness(3차 모멘트) + kurtosis(4차 모멘트)."""
        sql = """
            WITH stats AS (
                SELECT
                    CASE
                        WHEN presume_price < 200000000 THEN '2억 미만'
                        WHEN presume_price < 300000000 THEN '2~3억'
                        WHEN presume_price < 1000000000 THEN '3~10억'
                        WHEN presume_price < 5000000000 THEN '10~50억'
                        ELSE '50~100억'
                    END AS segment,
                    ratio,
                    AVG(ratio) OVER (PARTITION BY
                        CASE
                            WHEN presume_price < 200000000 THEN '2억 미만'
                            WHEN presume_price < 300000000 THEN '2~3억'
                            WHEN presume_price < 1000000000 THEN '3~10억'
                            WHEN presume_price < 5000000000 THEN '10~50억'
                            ELSE '50~100억'
                        END
                    ) AS mean_ratio,
                    STDDEV(ratio) OVER (PARTITION BY
                        CASE
                            WHEN presume_price < 200000000 THEN '2억 미만'
                            WHEN presume_price < 300000000 THEN '2~3억'
                            WHEN presume_price < 1000000000 THEN '3~10억'
                            WHEN presume_price < 5000000000 THEN '10~50억'
                            ELSE '50~100억'
                        END
                    ) AS std_ratio
                FROM _eda_base
            )
            SELECT
                segment,
                COUNT(*) AS cnt,
                AVG(POWER((ratio - mean_ratio) / NULLIF(std_ratio, 0), 3))
                    AS skewness,
                AVG(POWER((ratio - mean_ratio) / NULLIF(std_ratio, 0), 4)) - 3
                    AS excess_kurtosis
            FROM stats
            WHERE std_ratio > 0
            GROUP BY segment
            ORDER BY MIN(
                CASE segment
                    WHEN '2억 미만' THEN 1
                    WHEN '2~3억' THEN 2
                    WHEN '3~10억' THEN 3
                    WHEN '10~50억' THEN 4
                    ELSE 5
                END
            )
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c.name for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _print_distribution_shape(self, data: list[dict]):
        self.stdout.write(
            f"  {'세그먼트':<10s} {'건수':>10s} {'왜도':>8s} {'첨도':>10s} {'해석':<20s}"
        )
        for row in data:
            skew = row["skewness"] or 0
            kurt = row["excess_kurtosis"] or 0

            # 해석
            if skew < -0.5:
                skew_desc = "좌편향(저비율쏠림)"
            elif skew > 0.5:
                skew_desc = "우편향(고비율쏠림)"
            else:
                skew_desc = "대칭"

            if kurt > 1:
                kurt_desc = "+뾰족(집중)"
            elif kurt < -1:
                kurt_desc = "+완만(분산)"
            else:
                kurt_desc = "정규분포유사"

            self.stdout.write(
                f"  {row['segment']:<10s} {row['cnt']:>10,d} "
                f"{skew:>8.3f} {kurt:>10.3f} "
                f"{skew_desc}/{kurt_desc}"
            )

    # ──────────────────────────────────────────
    # 6. 월별 경쟁 강도 추이
    # ──────────────────────────────────────────

    def _analyze_monthly_competition(self) -> list[dict]:
        """BidContract JOIN으로 월별 경쟁 강도 집계."""
        sql = """
            SELECT
                LEFT(c.openg_date, 6) AS month,
                COUNT(DISTINCT (b.bid_ntce_no, b.bid_ntce_ord)) AS announcement_cnt,
                COUNT(*) AS bid_cnt,
                AVG(b.bidder_cnt) AS avg_bidder_cnt,
                AVG(b.ratio) AS avg_ratio,
                STDDEV(b.ratio) AS std_ratio,
                AVG(CASE WHEN b.openg_rank = '1' THEN b.ratio END) AS rank1_avg_ratio
            FROM _eda_base b
            JOIN g2b_bidcontract c
                ON b.bid_ntce_no = c.bid_ntce_no
                AND b.bid_ntce_ord = c.bid_ntce_ord
            WHERE c.openg_date != ''
              AND LENGTH(c.openg_date) >= 6
            GROUP BY month
            HAVING COUNT(*) >= 100
            ORDER BY month
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cols = [c.name for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _print_monthly_competition(self, data: list[dict]):
        if not data:
            self.stdout.write("  (데이터 없음)")
            return
        self.stdout.write(
            f"  {'월':>8s} {'공고수':>8s} {'입찰수':>10s} "
            f"{'평균참여':>8s} {'평균비율':>8s} {'1순위비율':>10s}"
        )
        for row in data:
            r1_avg = (
                f"{row['rank1_avg_ratio']:.2f}"
                if row["rank1_avg_ratio"] else "-"
            )
            self.stdout.write(
                f"  {row['month']:>8s} {row['announcement_cnt']:>8d} "
                f"{row['bid_cnt']:>10,d} "
                f"{(row['avg_bidder_cnt'] or 0):>8.1f} "
                f"{row['avg_ratio']:>8.2f} {r1_avg:>10s}"
            )

    # ──────────────────────────────────────────
    # JSON 저장
    # ──────────────────────────────────────────

    def _save_json(self, results: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path

        path.parent.mkdir(parents=True, exist_ok=True)

        # float 직렬화 처리
        def _clean(obj):
            if isinstance(obj, float):
                if obj != obj:  # NaN
                    return None
                return round(obj, 6)
            if isinstance(obj, dict):
                return {k: _clean(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_clean(v) for v in obj]
            return obj

        report = {
            "meta": {
                "command": "analyze_competitor_behavior",
                "bc_id": "BC-34",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "description": "Phase 2 심층 EDA: 경쟁자 행동 분석",
            },
            "base_count": results["base_count"],
            "segment_distribution": _clean(results["segment_distribution"]),
            "ratio_histogram": _clean(results["ratio_histogram"]),
            "company_profiles": _clean(results["company_profiles"]),
            "bidder_count_cross": _clean(results["bidder_count_cross"]),
            "distribution_shape": _clean(results["distribution_shape"]),
            "monthly_competition": _clean(results["monthly_competition"]),
        }

        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"JSON 저장: {path}"))
