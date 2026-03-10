"""BC-51: 컨설팅 업체 클러스터링 — Phase 1 Go/No-Go 탐색.

같은 컨설팅 업체를 쓰는 건설사들이 동일 공고에서 비슷한 투찰율(bid_rate)로
투찰하고, 이 패턴이 반복되는지를 통계적으로 판정(Go/No-Go).

산출물: JSON 결과 + 히스토그램 PNG 3장

사용:
    python manage.py explore_bid_clustering
    python manage.py explore_bid_clustering --area 경남 --months 6
    python manage.py explore_bid_clustering --task 0,1,2
    python manage.py explore_bid_clustering --parent-bizno 1234567890
"""

from __future__ import annotations

import json
import random
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UNIT_EOUK = 1_0000_0000

# 지역 약칭 -> demand_org_area 접두사 매핑
AREA_MAP = {
    "경남": "경상남도",
    "경북": "경상북도",
    "경기": "경기도",
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "제주": "제주특별자치도",
}


def _clean(obj):
    """Recursively clean floats (NaN->None, round to 6 decimals)."""
    if isinstance(obj, float):
        if obj != obj:  # NaN
            return None
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


class Command(BaseCommand):
    help = "BC-51: 컨설팅 업체 클러스터링 탐색 (Go/No-Go)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--area", type=str, default="경남",
            help="지역 필터 (기본: 경남, 'all'=전국)",
        )
        parser.add_argument(
            "--months", type=int, default=6,
            help="최근 N개월 (기본: 6)",
        )
        parser.add_argument(
            "--max-price", type=float, default=10,
            help="추정가격 상한 (억, 기본: 10)",
        )
        parser.add_argument(
            "--min-bidders", type=int, default=30,
            help="최소 입찰자수 (기본: 30)",
        )
        parser.add_argument(
            "--parent-bizno", type=str, default="",
            help="부모님 회사 사업자번호 (Task 4용, 선택)",
        )
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 경로 (기본: data/collected/bid_clustering_exploration.json)",
        )
        parser.add_argument(
            "--task", type=str, default="",
            help="특정 태스크만 실행 (0,1,2,3,4 콤마구분)",
        )
        parser.add_argument(
            "--collected-only", action="store_true",
            help="API 수집 완료된 공고만 대상 (BidApiCollectionLog 기준)",
        )

    def handle(self, *args, **options):
        self.area = options["area"]
        self.months = options["months"]
        self.max_price = options["max_price"]
        self.min_bidders = options["min_bidders"]
        self.parent_bizno = options["parent_bizno"]
        self.collected_only = options["collected_only"]
        output_path = (
            options["output"]
            or "data/collected/bid_clustering_exploration.json"
        )

        # 태스크 선택
        if options["task"]:
            tasks = [int(t.strip()) for t in options["task"].split(",")]
        else:
            tasks = [0, 1, 2, 3]
            if self.parent_bizno:
                tasks.append(4)

        self.stdout.write("=" * 70)
        self.stdout.write("  BC-51: 컨설팅 업체 클러스터링 탐색 (Go/No-Go)")
        self.stdout.write("=" * 70)
        self.stdout.write(f"  지역: {self.area}, 기간: 최근 {self.months}개월")
        self.stdout.write(
            f"  가격상한: {self.max_price}억, 최소참여: {self.min_bidders}명"
        )
        if self.collected_only:
            self.stdout.write("  필터: API 수집 완료 공고만 (--collected-only)")
        self.stdout.write(f"  태스크: {tasks}")
        self.stdout.write("")

        results: dict[str, Any] = {
            "params": {
                "area": self.area,
                "months": self.months,
                "max_price_eouk": self.max_price,
                "min_bidders": self.min_bidders,
                "parent_bizno": self.parent_bizno or None,
            },
        }

        try:
            if 0 in tasks:
                self.stdout.write(f"\n{'─' * 60}")
                self.stdout.write("  [Task 0] 데이터 스코프 확인")
                self.stdout.write(f"{'─' * 60}")
                results["task0_scope_check"] = self._task0_scope_check()

            if 1 in tasks:
                self.stdout.write(f"\n{'─' * 60}")
                self.stdout.write("  [Task 1] 스코프 축소 + temp table 생성")
                self.stdout.write(f"{'─' * 60}")
                results["task1_base_table"] = self._task1_create_base()

            if 2 in tasks:
                self.stdout.write(f"\n{'─' * 60}")
                self.stdout.write("  [Task 2] 히스토그램 + 피크 탐지")
                self.stdout.write(f"{'─' * 60}")
                results["task2_histograms"] = self._task2_histograms()

            if 3 in tasks:
                self.stdout.write(f"\n{'─' * 60}")
                self.stdout.write("  [Task 3] 일관성 분석 + 퍼뮤테이션 테스트")
                self.stdout.write(f"{'─' * 60}")
                results["task3_consistency"] = self._task3_consistency()

            if 4 in tasks and self.parent_bizno:
                self.stdout.write(f"\n{'─' * 60}")
                self.stdout.write("  [Task 4] 부모님 회사 스팟 체크")
                self.stdout.write(f"{'─' * 60}")
                results["task4_parent_check"] = self._task4_parent_check()

            # Verdict
            results["verdict"] = self._verdict(results)
            self._print_verdict(results["verdict"])

        finally:
            self._drop_base_table()

        self._save_json(results, output_path)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("  BC-51 완료"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

    # ──────────────────────────────────────────
    # Task 0: 데이터 스코프 확인
    # ──────────────────────────────────────────

    def _task0_scope_check(self) -> dict:
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM g2b_bidresult")
            total_results = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM g2b_bidresult "
                "WHERE bid_rate IS NOT NULL AND bid_rate > 0"
            )
            valid_bid_rate = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM g2b_bidcontract")
            total_contracts = cur.fetchone()[0]

            # 조인 가능 건수
            cur.execute("""
                SELECT COUNT(DISTINCT (r.bid_ntce_no, r.bid_ntce_ord))
                FROM g2b_bidresult r
                INNER JOIN g2b_bidcontract c
                    ON r.bid_ntce_no = c.bid_ntce_no
                    AND r.bid_ntce_ord = c.bid_ntce_ord
                WHERE r.bid_rate > 0
            """)
            joinable = cur.fetchone()[0]

        result = {
            "total_bidresult": total_results,
            "valid_bid_rate": valid_bid_rate,
            "bid_rate_ratio": round(valid_bid_rate / max(total_results, 1) * 100, 1),
            "total_bidcontract": total_contracts,
            "joinable_announcements": joinable,
        }

        self.stdout.write(f"  BidResult 전체: {total_results:,}건")
        self.stdout.write(
            f"  bid_rate 유효: {valid_bid_rate:,}건 "
            f"({result['bid_rate_ratio']}%)"
        )
        self.stdout.write(f"  BidContract: {total_contracts:,}건")
        self.stdout.write(f"  조인 가능 공고: {joinable:,}건")

        return result

    # ──────────────────────────────────────────
    # Task 1: 스코프 축소 + temp table 생성
    # ──────────────────────────────────────────

    def _task1_create_base(self) -> dict:
        max_price_won = int(self.max_price * UNIT_EOUK)
        cutoff = (
            datetime.now() - timedelta(days=self.months * 30)
        ).strftime("%Y%m%d")

        area_filter = self._area_filter()

        count = self._create_base_table(
            max_price_won, cutoff, area_filter,
        )

        # 자동 확장: 공고 100개 미만
        expanded = False
        original_params = {
            "area": self.area, "months": self.months,
        }

        if count < 100:
            self.stdout.write(
                f"  공고 {count}개 < 100 — 지역 필터 제거"
            )
            self._drop_base_table()
            area_filter = ""
            count = self._create_base_table(
                max_price_won, cutoff, area_filter,
            )
            expanded = True

        if count < 100:
            self.stdout.write(
                f"  여전히 {count}개 < 100 — 기간 12개월로 확장"
            )
            self._drop_base_table()
            cutoff = (
                datetime.now() - timedelta(days=365)
            ).strftime("%Y%m%d")
            count = self._create_base_table(
                max_price_won, cutoff, area_filter,
            )
            expanded = True

        # 고유 공고 수
        with connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(DISTINCT (bid_ntce_no, bid_ntce_ord))
                FROM _cluster_base
            """)
            unique_announcements = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(DISTINCT company_bizno)
                FROM _cluster_base
                WHERE company_bizno != ''
            """)
            unique_companies = cur.fetchone()[0]

        result = {
            "row_count": count,
            "unique_announcements": unique_announcements,
            "unique_companies": unique_companies,
            "expanded": expanded,
            "original_params": original_params,
        }

        self.stdout.write(f"  _cluster_base: {count:,}건")
        self.stdout.write(f"  고유 공고: {unique_announcements:,}개")
        self.stdout.write(f"  고유 업체: {unique_companies:,}개")
        if expanded:
            self.stdout.write(
                self.style.WARNING("  (스코프 자동 확장됨)")
            )

        return result

    def _area_filter(self) -> str:
        if self.area.lower() == "all" or not self.area:
            return ""
        prefix = AREA_MAP.get(self.area, self.area)
        return f"AND c.demand_org_area LIKE '{prefix}%%'"

    def _create_base_table(
        self, max_price_won: int, cutoff: str, area_filter: str,
    ) -> int:
        """2-stage: BidResult 필터 먼저 -> BidContract 조인."""
        with connection.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS _cluster_base")
            cur.execute("DROP TABLE IF EXISTS _cluster_r_filtered")

            # Stage 1: BidResult만 필터 (presume_price 인덱스 활용)
            collected_filter = ""
            if self.collected_only:
                collected_filter = """
                  AND (bid_ntce_no, bid_ntce_ord) IN (
                      SELECT bid_ntce_no, bid_ntce_ord
                      FROM g2b_bidapicollectionlog
                  )
                """
                self.stdout.write("    Stage 1: BidResult 필터링 (수집 공고만)...")
            else:
                self.stdout.write("    Stage 1: BidResult 필터링...")
            cur.execute(f"""
                CREATE TEMP TABLE _cluster_r_filtered AS
                SELECT bid_ntce_no, bid_ntce_ord,
                       company_bizno, company_nm, bid_rate,
                       bidder_cnt, openg_rank, presume_price
                FROM g2b_bidresult
                WHERE bid_rate > 0
                  AND bidder_cnt >= {self.min_bidders}
                  AND presume_price > 0
                  AND presume_price < {max_price_won}
                  {collected_filter}
            """)
            cur.execute(
                "CREATE INDEX ON _cluster_r_filtered "
                "(bid_ntce_no, bid_ntce_ord)"
            )
            cur.execute(
                "SELECT COUNT(*) FROM _cluster_r_filtered"
            )
            stage1_count = cur.fetchone()[0]
            self.stdout.write(f"    Stage 1: {stage1_count:,}건")

            # Stage 2: BidContract 조인 (필터된 소규모 집합)
            self.stdout.write("    Stage 2: BidContract 조인...")
            cur.execute(f"""
                CREATE TEMP TABLE _cluster_base AS
                SELECT r.bid_ntce_no, r.bid_ntce_ord,
                       r.company_bizno, r.company_nm, r.bid_rate,
                       r.bidder_cnt, r.openg_rank, r.presume_price,
                       c.demand_org_area, c.openg_date
                FROM _cluster_r_filtered r
                INNER JOIN LATERAL (
                    SELECT demand_org_area, openg_date
                    FROM g2b_bidcontract
                    WHERE bid_ntce_no = r.bid_ntce_no
                      AND bid_ntce_ord = r.bid_ntce_ord
                      AND openg_date != ''
                      AND openg_date < '99990000'
                    ORDER BY openg_date DESC
                    LIMIT 1
                ) c ON true
                WHERE c.openg_date >= '{cutoff}'
                  {area_filter}
            """)

            cur.execute("DROP TABLE IF EXISTS _cluster_r_filtered")
            cur.execute(
                "CREATE INDEX ON _cluster_base "
                "(bid_ntce_no, bid_ntce_ord)"
            )
            cur.execute(
                "CREATE INDEX ON _cluster_base (company_bizno)"
            )
            cur.execute("SELECT COUNT(*) FROM _cluster_base")
            return cur.fetchone()[0]

    def _drop_base_table(self):
        with connection.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS _cluster_base")
            cur.execute("DROP TABLE IF EXISTS _cluster_r_filtered")
            cur.execute("DROP TABLE IF EXISTS _cluster_frequent")

    # ──────────────────────────────────────────
    # Task 2: 히스토그램 + 피크 탐지
    # ──────────────────────────────────────────

    def _task2_histograms(self) -> dict:
        # 참여자 100명+ 공고 3개 선택 (시간 간격 분산)
        with connection.cursor() as cur:
            cur.execute("""
                SELECT bid_ntce_no, bid_ntce_ord, bidder_cnt,
                       MAX(openg_date) AS openg_date
                FROM _cluster_base
                WHERE bidder_cnt >= 100
                GROUP BY bid_ntce_no, bid_ntce_ord, bidder_cnt
                ORDER BY MAX(openg_date)
            """)
            candidates = cur.fetchall()

        if len(candidates) < 3:
            # 100명 미만이라도 가장 많은 참여자 공고 선택
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT bid_ntce_no, bid_ntce_ord, bidder_cnt,
                           MAX(openg_date) AS openg_date
                    FROM _cluster_base
                    GROUP BY bid_ntce_no, bid_ntce_ord, bidder_cnt
                    ORDER BY bidder_cnt DESC
                    LIMIT 10
                """)
                candidates = cur.fetchall()

        # 시간 분산을 위해 앞/중/뒤에서 선택
        if len(candidates) >= 3:
            selected = [
                candidates[0],
                candidates[len(candidates) // 2],
                candidates[-1],
            ]
        else:
            selected = candidates[:3]

        if not selected:
            self.stdout.write(self.style.WARNING("  공고 없음 — 히스토그램 생략"))
            return {"announcements": [], "note": "no announcements found"}

        histograms = []
        for ntce_no, ntce_ord, bidder_cnt, openg_date in selected:
            hist = self._single_announcement_histogram(
                ntce_no, ntce_ord,
            )
            peaks = self._detect_peaks(hist)

            entry = {
                "bid_ntce_no": ntce_no,
                "bid_ntce_ord": ntce_ord,
                "bidder_cnt": bidder_cnt,
                "openg_date": openg_date,
                "histogram": hist,
                "peaks": peaks,
            }
            histograms.append(entry)

            self.stdout.write(
                f"  공고 {ntce_no}-{ntce_ord} "
                f"(참여 {bidder_cnt}명, {openg_date})"
            )
            self.stdout.write(
                f"    피크 {len(peaks)}개: "
                + ", ".join(
                    f"{p['bin_center']:.2f}% (z={p['z_score']:.1f})"
                    for p in peaks
                )
            )

        # 차트 생성
        self._save_histogram_charts(histograms)

        return {"announcements": histograms}

    def _single_announcement_histogram(
        self, ntce_no: str, ntce_ord: str,
    ) -> list[dict]:
        """0.01%p 단위 히스토그램 (WIDTH_BUCKET, 86~94%)."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    WIDTH_BUCKET(
                        bid_rate::float, 86, 94, 800
                    ) AS bucket,
                    COUNT(*) AS cnt
                FROM _cluster_base
                WHERE bid_ntce_no = %s AND bid_ntce_ord = %s
                  AND bid_rate BETWEEN 86 AND 94
                GROUP BY bucket
                ORDER BY bucket
            """, [ntce_no, ntce_ord])

            rows = cur.fetchall()

        # bucket -> bin_center
        result = []
        for bucket, cnt in rows:
            if bucket < 1 or bucket > 800:
                continue
            bin_center = 86 + (bucket - 0.5) * (94 - 86) / 800
            result.append({
                "bucket": bucket,
                "bin_center": round(bin_center, 4),
                "cnt": cnt,
            })
        return result

    def _detect_peaks(self, histogram: list[dict]) -> list[dict]:
        """z-score 기반 local-max detection."""
        if len(histogram) < 5:
            return []

        counts = [h["cnt"] for h in histogram]
        mean = statistics.mean(counts)
        stdev = statistics.stdev(counts) if len(counts) > 1 else 1.0
        if stdev == 0:
            return []

        peaks = []
        for i, h in enumerate(histogram):
            z = (h["cnt"] - mean) / stdev
            if z <= 2.0:
                continue
            # 양옆보다 높은지 확인
            left = histogram[i - 1]["cnt"] if i > 0 else 0
            right = histogram[i + 1]["cnt"] if i < len(histogram) - 1 else 0
            if h["cnt"] > left and h["cnt"] > right:
                peaks.append({
                    "bucket": h["bucket"],
                    "bin_center": h["bin_center"],
                    "cnt": h["cnt"],
                    "z_score": round(z, 2),
                })

        return peaks

    def _save_histogram_charts(self, histograms: list[dict]):
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
        except ImportError:
            self.stderr.write("  matplotlib 미설치 — 차트 생략")
            return

        plt.rcParams["axes.unicode_minus"] = False
        for font_name in ["AppleGothic", "Malgun Gothic", "NanumGothic"]:
            if any(font_name in f.name for f in fm.fontManager.ttflist):
                plt.rcParams["font.family"] = font_name
                break

        chart_dir = BASE_DIR / "data" / "collected" / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)

        for idx, entry in enumerate(histograms):
            hist = entry["histogram"]
            peaks = entry["peaks"]
            if not hist:
                continue

            fig, ax = plt.subplots(figsize=(14, 5))
            centers = [h["bin_center"] for h in hist]
            counts = [h["cnt"] for h in hist]

            ax.bar(centers, counts, width=0.01, color="#4a90d9", alpha=0.7)

            # 피크 마킹
            for p in peaks:
                ax.axvline(
                    p["bin_center"], color="red",
                    linestyle="--", alpha=0.7,
                )
                ax.annotate(
                    f"{p['bin_center']:.2f}%\nz={p['z_score']:.1f}",
                    xy=(p["bin_center"], p["cnt"]),
                    xytext=(0, 15),
                    textcoords="offset points",
                    ha="center", fontsize=8, color="red",
                    arrowprops=dict(arrowstyle="->", color="red"),
                )

            ax.set_xlabel("bid_rate (%)")
            ax.set_ylabel("count")
            ax.set_title(
                f"Bid Rate Distribution: "
                f"{entry['bid_ntce_no']}-{entry['bid_ntce_ord']} "
                f"(n={entry['bidder_cnt']}, {entry['openg_date']})"
            )
            ax.grid(axis="y", alpha=0.3)

            filename = f"clustering_histogram_{idx + 1}.png"
            fig.savefig(
                chart_dir / filename,
                dpi=150, bbox_inches="tight",
            )
            plt.close(fig)
            self.stdout.write(f"  차트: {filename}")

    # ──────────────────────────────────────────
    # Task 3: 일관성 분석 + 퍼뮤테이션 테스트
    # ──────────────────────────────────────────

    def _task3_consistency(self) -> dict:
        result = {}

        # 3-1. 공고별 피크 -> 전역 핫스팟
        self.stdout.write("  [3-1] 공고별 피크 -> 전역 핫스팟")
        hotspots = self._task3_1_hotspots()
        result["hotspots"] = hotspots
        self.stdout.write(f"    핫스팟 {len(hotspots['top_hotspots'])}개 발견")

        # 3-2. 업체 쌍 근접도
        self.stdout.write("  [3-2] 업체 쌍 근접도 (co-occurrence)")
        pairs = self._task3_2_pairs()
        result["pairs"] = pairs
        self.stdout.write(
            f"    근접 쌍 {pairs['pair_count']}개 (avg_diff < 0.5%p)"
        )

        # 3-3. 퍼뮤테이션 테스트
        self.stdout.write("  [3-3] 퍼뮤테이션 테스트 (100회)")
        perm = self._task3_3_permutation(pairs["pair_count"])
        result["permutation_test"] = perm
        self.stdout.write(
            f"    관측값: {perm['observed']}, "
            f"null 평균: {perm['null_mean']:.1f}, "
            f"null 95th: {perm['null_p95']:.1f}"
        )
        self.stdout.write(
            f"    p-value: {perm['p_value']:.4f}, "
            f"z-score: {perm['z_score']:.2f}"
        )

        return result

    def _task3_1_hotspots(self) -> dict:
        """전체 공고의 0.05%p 히스토그램 -> 공고별 피크 -> 전역 핫스팟."""
        with connection.cursor() as cur:
            # 공고별 0.05%p 히스토그램
            cur.execute("""
                SELECT bid_ntce_no, bid_ntce_ord,
                       WIDTH_BUCKET(bid_rate::float, 86, 94, 160) AS bucket,
                       COUNT(*) AS cnt
                FROM _cluster_base
                WHERE bid_rate BETWEEN 86 AND 94
                GROUP BY bid_ntce_no, bid_ntce_ord, bucket
                ORDER BY bid_ntce_no, bid_ntce_ord, bucket
            """)
            rows = cur.fetchall()

        # 공고별 그룹핑
        announcements: dict[tuple, list[tuple]] = {}
        for ntce_no, ntce_ord, bucket, cnt in rows:
            key = (ntce_no, ntce_ord)
            announcements.setdefault(key, []).append((bucket, cnt))

        # 공고별 피크 추출
        all_peak_buckets = []
        announcements_with_peaks = 0

        for key, bins in announcements.items():
            if len(bins) < 5:
                continue
            counts = [c for _, c in bins]
            mean = statistics.mean(counts)
            stdev = statistics.stdev(counts) if len(counts) > 1 else 1.0
            if stdev == 0:
                continue

            has_peak = False
            for i, (bucket, cnt) in enumerate(bins):
                z = (cnt - mean) / stdev
                if z <= 2.0:
                    continue
                left = bins[i - 1][1] if i > 0 else 0
                right = bins[i + 1][1] if i < len(bins) - 1 else 0
                if cnt > left and cnt > right:
                    all_peak_buckets.append(bucket)
                    has_peak = True

            if has_peak:
                announcements_with_peaks += 1

        # 전역 핫스팟: 피크 bucket 히스토그램
        if not all_peak_buckets:
            return {
                "total_announcements": len(announcements),
                "announcements_with_peaks": 0,
                "top_hotspots": [],
            }

        bucket_counts: dict[int, int] = {}
        for b in all_peak_buckets:
            bucket_counts[b] = bucket_counts.get(b, 0) + 1

        # 상위 핫스팟 (빈도순)
        sorted_hotspots = sorted(
            bucket_counts.items(), key=lambda x: -x[1],
        )
        top_hotspots = []
        for bucket, freq in sorted_hotspots[:20]:
            center = 86 + (bucket - 0.5) * (94 - 86) / 160
            top_hotspots.append({
                "bucket": bucket,
                "center_pct": round(center, 3),
                "frequency": freq,
            })

        return {
            "total_announcements": len(announcements),
            "announcements_with_peaks": announcements_with_peaks,
            "peak_rate": round(
                announcements_with_peaks / max(len(announcements), 1) * 100, 1,
            ),
            "top_hotspots": top_hotspots,
        }

    def _task3_2_pairs(self) -> dict:
        """업체 쌍 근접도. top-500 frequent 업체 + 별도 temp table로 DB OOM 방지."""
        with connection.cursor() as cur:
            # 5회+ 참여 업체 (top 500, 참여 빈도순)
            cur.execute("DROP TABLE IF EXISTS _cluster_frequent")
            cur.execute("""
                CREATE TEMP TABLE _cluster_frequent AS
                SELECT company_bizno
                FROM _cluster_base
                WHERE company_bizno != ''
                GROUP BY company_bizno
                HAVING COUNT(DISTINCT (bid_ntce_no, bid_ntce_ord)) >= 5
                ORDER BY COUNT(*) DESC
                LIMIT 500
            """)
            cur.execute(
                "CREATE INDEX ON _cluster_frequent (company_bizno)"
            )
            cur.execute("SELECT COUNT(*) FROM _cluster_frequent")
            frequent_count = cur.fetchone()[0]
            self.stdout.write(f"    5회+ 참여 업체 (top 500): {frequent_count}개")

            if frequent_count < 2:
                return {
                    "frequent_companies": frequent_count,
                    "pair_count": 0,
                    "top_pairs": [],
                }

            # frequent 업체 데이터만 별도 temp table 추출
            cur.execute("DROP TABLE IF EXISTS _cluster_freq_data")
            cur.execute("""
                CREATE TEMP TABLE _cluster_freq_data AS
                SELECT b.bid_ntce_no, b.bid_ntce_ord,
                       b.company_bizno, b.bid_rate
                FROM _cluster_base b
                INNER JOIN _cluster_frequent f
                    ON b.company_bizno = f.company_bizno
            """)
            cur.execute(
                "CREATE INDEX ON _cluster_freq_data "
                "(bid_ntce_no, bid_ntce_ord)"
            )
            cur.execute("SELECT COUNT(*) FROM _cluster_freq_data")
            freq_data_count = cur.fetchone()[0]
            self.stdout.write(f"    freq 데이터: {freq_data_count:,}건")

            # self-join on small temp table
            cur.execute("""
                SELECT a.company_bizno AS biz_a,
                       b.company_bizno AS biz_b,
                       COUNT(*) AS co_count,
                       AVG(ABS(a.bid_rate - b.bid_rate)) AS avg_rate_diff
                FROM _cluster_freq_data a
                INNER JOIN _cluster_freq_data b
                    ON a.bid_ntce_no = b.bid_ntce_no
                    AND a.bid_ntce_ord = b.bid_ntce_ord
                    AND a.company_bizno < b.company_bizno
                GROUP BY a.company_bizno, b.company_bizno
                HAVING COUNT(*) >= 3
                    AND AVG(ABS(a.bid_rate - b.bid_rate)) < 0.5
                ORDER BY avg_rate_diff
                LIMIT 200
            """)
            pair_rows = cur.fetchall()
            cur.execute("DROP TABLE IF EXISTS _cluster_freq_data")

        top_pairs = []
        for biz_a, biz_b, co_count, avg_diff in pair_rows[:30]:
            top_pairs.append({
                "biz_a": biz_a,
                "biz_b": biz_b,
                "co_count": co_count,
                "avg_rate_diff": round(float(avg_diff), 4),
            })

        result = {
            "frequent_companies": frequent_count,
            "pair_count": len(pair_rows),
            "top_pairs": top_pairs,
        }

        # 상위 5쌍 출력
        if top_pairs:
            self.stdout.write("    상위 근접 쌍:")
            for p in top_pairs[:5]:
                self.stdout.write(
                    f"      {p['biz_a']} - {p['biz_b']}: "
                    f"공동참여 {p['co_count']}회, "
                    f"평균차이 {p['avg_rate_diff']:.4f}%p"
                )

        return result

    def _task3_3_permutation(self, observed_count: int) -> dict:
        """퍼뮤테이션 테스트: 100회 셔플로 null distribution 생성.

        메모리 보호: frequent 업체가 2명+ 참여하는 공고만, 최대 500개 샘플.
        """
        # frequent 업체가 2명+ 있는 공고만 추출 (SQL에서 필터)
        with connection.cursor() as cur:
            cur.execute("""
                SELECT b.bid_ntce_no, b.bid_ntce_ord,
                       b.company_bizno, b.bid_rate::float
                FROM _cluster_base b
                INNER JOIN _cluster_frequent f
                    ON b.company_bizno = f.company_bizno
                WHERE (b.bid_ntce_no, b.bid_ntce_ord) IN (
                    SELECT b2.bid_ntce_no, b2.bid_ntce_ord
                    FROM _cluster_base b2
                    INNER JOIN _cluster_frequent f2
                        ON b2.company_bizno = f2.company_bizno
                    GROUP BY b2.bid_ntce_no, b2.bid_ntce_ord
                    HAVING COUNT(*) >= 2
                    ORDER BY RANDOM()
                    LIMIT 500
                )
                ORDER BY b.bid_ntce_no, b.bid_ntce_ord
            """)
            rows = cur.fetchall()

        self.stdout.write(
            f"    퍼뮤테이션 대상: {len(rows):,}건 "
            f"(frequent 업체 2명+ 공고, 최대 500개)"
        )

        if not rows:
            return self._empty_permutation_result(observed_count)

        # 공고별 그룹핑
        by_announcement: dict[tuple, list[tuple]] = {}
        for ntce_no, ntce_ord, bizno, rate in rows:
            key = (ntce_no, ntce_ord)
            by_announcement.setdefault(key, []).append((bizno, rate))

        self.stdout.write(
            f"    공고 {len(by_announcement)}개, "
            f"평균 {len(rows) / max(len(by_announcement), 1):.1f}명/공고"
        )

        # 퍼뮤테이션 100회
        rng = random.Random(42)
        null_counts = []

        for trial in range(100):
            # 각 공고 내에서 bid_rate만 셔플
            pair_diffs: dict[tuple, list[float]] = {}
            for key, entries in by_announcement.items():
                rates = [e[1] for e in entries]
                rng.shuffle(rates)
                biznos = [e[0] for e in entries]

                for i in range(len(biznos)):
                    for j in range(i + 1, len(biznos)):
                        pair_key = (
                            (biznos[i], biznos[j])
                            if biznos[i] < biznos[j]
                            else (biznos[j], biznos[i])
                        )
                        pair_diffs.setdefault(pair_key, []).append(
                            abs(rates[i] - rates[j])
                        )

            # 기준: co_count >= 3, avg_diff < 0.5
            cnt = sum(
                1 for diffs in pair_diffs.values()
                if len(diffs) >= 3
                and statistics.mean(diffs) < 0.5
            )
            null_counts.append(cnt)

            if (trial + 1) % 25 == 0:
                self.stdout.write(f"    셔플 {trial + 1}/100 완료")

        null_mean = statistics.mean(null_counts)
        null_stdev = (
            statistics.stdev(null_counts) if len(null_counts) > 1 else 1.0
        )
        null_sorted = sorted(null_counts)
        null_p95 = null_sorted[int(len(null_sorted) * 0.95)]

        z_score = (
            (observed_count - null_mean) / null_stdev
            if null_stdev > 0 else 0.0
        )
        p_value = sum(
            1 for c in null_counts if c >= observed_count
        ) / len(null_counts)

        return {
            "observed": observed_count,
            "null_mean": round(null_mean, 2),
            "null_stdev": round(null_stdev, 2),
            "null_p95": round(float(null_p95), 2),
            "null_min": min(null_counts),
            "null_max": max(null_counts),
            "z_score": round(z_score, 2),
            "p_value": round(p_value, 4),
            "n_permutations": 100,
        }

    def _empty_permutation_result(self, observed_count: int) -> dict:
        self.stdout.write(
            self.style.WARNING("    frequent 업체 공동참여 공고 없음 — 퍼뮤테이션 생략")
        )
        return {
            "observed": observed_count,
            "null_mean": 0,
            "null_stdev": 0,
            "null_p95": 0,
            "null_min": 0,
            "null_max": 0,
            "z_score": 0.0,
            "p_value": 1.0,
            "n_permutations": 0,
            "note": "no eligible announcements for permutation",
        }

    # ──────────────────────────────────────────
    # Task 4: 부모님 회사 스팟 체크
    # ──────────────────────────────────────────

    def _task4_parent_check(self) -> dict:
        bizno = self.parent_bizno
        with connection.cursor() as cur:
            # 부모님 회사 bid_rate 분포
            cur.execute("""
                SELECT bid_rate::float, bid_ntce_no, bid_ntce_ord,
                       openg_rank, bidder_cnt
                FROM _cluster_base
                WHERE company_bizno = %s
                ORDER BY bid_rate
            """, [bizno])
            parent_rows = cur.fetchall()

            if not parent_rows:
                self.stdout.write(
                    f"  사업자번호 {bizno}: 데이터 없음"
                )
                return {"bizno": bizno, "count": 0}

            rates = [r[0] for r in parent_rows]
            avg_rate = statistics.mean(rates)
            std_rate = statistics.stdev(rates) if len(rates) > 1 else 0.0

            # 가장 가까운 이웃
            cur.execute("""
                SELECT b.company_bizno,
                       MAX(b.company_nm) AS company_nm,
                       COUNT(*) AS co_count,
                       AVG(ABS(a.bid_rate - b.bid_rate)) AS avg_diff
                FROM _cluster_base a
                INNER JOIN _cluster_base b
                    ON a.bid_ntce_no = b.bid_ntce_no
                    AND a.bid_ntce_ord = b.bid_ntce_ord
                    AND a.company_bizno != b.company_bizno
                WHERE a.company_bizno = %s
                  AND b.company_bizno != ''
                GROUP BY b.company_bizno
                HAVING COUNT(*) >= 2
                ORDER BY AVG(ABS(a.bid_rate - b.bid_rate))
                LIMIT 10
            """, [bizno])
            neighbors = cur.fetchall()

        neighbor_list = []
        for nbizno, nm, co_count, avg_diff in neighbors:
            neighbor_list.append({
                "bizno": nbizno,
                "name": nm,
                "co_count": co_count,
                "avg_rate_diff": round(float(avg_diff), 4),
            })

        result = {
            "bizno": bizno,
            "count": len(parent_rows),
            "avg_rate": round(avg_rate, 4),
            "std_rate": round(std_rate, 4),
            "min_rate": round(min(rates), 4),
            "max_rate": round(max(rates), 4),
            "nearest_neighbors": neighbor_list,
        }

        self.stdout.write(f"  사업자번호: {bizno}")
        self.stdout.write(f"  투찰 {len(parent_rows)}건")
        self.stdout.write(
            f"  bid_rate: 평균 {avg_rate:.2f}%, "
            f"std {std_rate:.2f}%"
        )
        if neighbor_list:
            self.stdout.write("  가장 가까운 이웃:")
            for n in neighbor_list[:5]:
                self.stdout.write(
                    f"    {n['name']}: "
                    f"공동 {n['co_count']}회, "
                    f"차이 {n['avg_rate_diff']:.4f}%p"
                )

        return result

    # ──────────────────────────────────────────
    # Verdict 판정
    # ──────────────────────────────────────────

    def _verdict(self, results: dict) -> dict:
        perm = (results.get("task3_consistency") or {}).get(
            "permutation_test", {},
        )
        p_value = perm.get("p_value", 1.0)
        z_score = perm.get("z_score", 0.0)
        observed = perm.get("observed", 0)

        hotspots = (results.get("task3_consistency") or {}).get(
            "hotspots", {},
        )
        peak_rate = hotspots.get("peak_rate", 0)

        if p_value < 0.05 and z_score > 2.0:
            decision = "GO"
            reason = (
                f"p={p_value:.4f} < 0.05, z={z_score:.2f} > 2.0 "
                f"— 통계적으로 유의한 클러스터링 신호"
            )
        elif p_value < 0.10:
            decision = "MARGINAL"
            reason = (
                f"p={p_value:.4f} < 0.10 — 경계선. "
                f"추가 데이터 또는 기간 확장 권장"
            )
        else:
            decision = "NO-GO"
            reason = (
                f"p={p_value:.4f} >= 0.10 — "
                f"클러스터링 신호 부족"
            )

        return {
            "decision": decision,
            "reason": reason,
            "p_value": p_value,
            "z_score": z_score,
            "observed_pairs": observed,
            "peak_rate_pct": peak_rate,
        }

    def _print_verdict(self, verdict: dict):
        self.stdout.write(f"\n{'=' * 70}")
        self.stdout.write("  VERDICT")
        self.stdout.write(f"{'=' * 70}")

        decision = verdict["decision"]
        if decision == "GO":
            styled = self.style.SUCCESS(f"  >>> {decision} <<<")
        elif decision == "MARGINAL":
            styled = self.style.WARNING(f"  >>> {decision} <<<")
        else:
            styled = self.style.ERROR(f"  >>> {decision} <<<")

        self.stdout.write(styled)
        self.stdout.write(f"  {verdict['reason']}")
        self.stdout.write(
            f"  관측 쌍: {verdict['observed_pairs']}, "
            f"p-value: {verdict['p_value']:.4f}, "
            f"z-score: {verdict['z_score']:.2f}"
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
                "command": "explore_bid_clustering",
                "bc_id": "BC-51",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "description": (
                    "컨설팅 업체 클러스터링 Go/No-Go 탐색"
                ),
            },
            **_clean(results),
        }

        path.write_text(
            json.dumps(
                report, ensure_ascii=False, indent=2, default=str,
            ),
            encoding="utf-8",
        )
        self.stdout.write(self.style.SUCCESS(f"\n  JSON 저장: {path}"))
