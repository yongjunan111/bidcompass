"""BC-37: 크로스테이블 종합 EDA + 세그먼트 정책 추출.

5개 테이블(BidResult 32M, BidContract 89만, BidApiAValue 479건,
BidApiPrelimPrice 8,422건, BidApiCollectionLog 958건) 크로스 조인으로
세그먼트별 투찰 정책 테이블을 생산한다.

3-Layer 아키텍처:
  A: 시장 행동 지도 (BidResult + BidContract)
  B: 업체 행동 시그니처 (BidResult 업체별)
  C: 메커니즘 캘리브레이션 (API + BidResult 1순위)
"""

from __future__ import annotations

import json
import math
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UNIT_EOUK = 1_0000_0000

ALL_MODULES = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]

# 세그먼트별 하한율 (bid_engine.py:184 FLOOR_RATE_TABLE, CONSTRUCTION 기준)
FLOOR_RATE_MAP = {
    "T5": 89.745, "T4": 89.745, "T3": 89.745,
    "T2A": 88.745, "T1": 87.495,
}

# 세그먼트별 만점 (bid_engine.py:152 TABLE_PARAMS_MAP)
MAX_SCORE_MAP = {"T5": 90, "T4": 90, "T3": 80, "T2A": 70, "T1": 50}


def _clean(obj):
    """Recursively clean floats (NaN→None, round to 6 decimals)."""
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
    help = "BC-37: 크로스테이블 종합 EDA + 세그먼트 정책 추출"

    def add_arguments(self, parser):
        parser.add_argument(
            "--module", type=str, default="",
            help="실행 모듈 (M1,M2,...콤마구분, 미지정시 전체)",
        )
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로",
        )

    def handle(self, *args, **options):
        modules = (
            [m.strip().upper() for m in options["module"].split(",") if m.strip()]
            if options["module"]
            else ALL_MODULES
        )
        invalid = [m for m in modules if m not in ALL_MODULES]
        if invalid:
            self.stderr.write(f"알 수 없는 모듈: {invalid}")
            return

        self.stdout.write("=" * 70)
        self.stdout.write("  BC-37: 크로스테이블 종합 EDA + 세그먼트 정책 추출")
        self.stdout.write("=" * 70)
        self.stdout.write(f"  실행 모듈: {', '.join(modules)}")
        self.stdout.write("")

        results: dict[str, Any] = {}

        try:
            base_count = self._create_cross_base()
            results["base_count"] = base_count

            if base_count < 1_000_000:
                self.stderr.write(
                    f"  ⚠️  _cross_base 행수 {base_count:,d} < 1M — 데이터 부족 주의"
                )

            dispatch = {
                "M1": self._m1_sampling_bias,
                "M2": self._m2_winrate_surface,
                "M3": self._m3_ratio_peaks,
                "M4": self._m4_competition_pressure,
                "M5": self._m5_company_archetypes,
                "M6": self._m6_regime_shift,
                "M7": self._m7_scenario_sensitivity,
                "M8": lambda: self._m8_policy_extraction(results),
            }

            for m in modules:
                self.stdout.write(f"\n{'─' * 60}")
                self.stdout.write(f"  {m} 실행 중...")
                self.stdout.write(f"{'─' * 60}")
                try:
                    results[m] = dispatch[m]()
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {m} 완료"))
                except Exception as e:
                    self.stderr.write(f"  ✗ {m} 실패: {e}")
                    results[m] = {"error": str(e)}

            # 차트 생성
            if any(m in results and "error" not in (results.get(m) or {})
                   for m in ["M2", "M3", "M4", "M5", "M6", "M7"]):
                self._save_charts(results)

        finally:
            self._drop_cross_base()

        output_path = options["output"] or "data/collected/cross_table_eda.json"
        self._save_json(results, output_path)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("  BC-37 완료"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

    # ──────────────────────────────────────────────
    # 임시테이블
    # ──────────────────────────────────────────────

    def _create_cross_base(self) -> int:
        """_cross_base 임시테이블 생성 (BidResult × BidContract)."""
        t0 = datetime.now()
        self.stdout.write("  _cross_base 생성 중... (BidResult × BidContract)")

        with connection.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS _cross_base")
            cur.execute("""
                CREATE TEMP TABLE _cross_base AS
                SELECT
                    r.bid_ntce_no, r.bid_ntce_ord,
                    r.company_bizno, r.company_nm,
                    r.presume_price, r.estimated_price, r.bid_amt,
                    r.openg_rank, r.bidder_cnt, r.success_lowest_rate,
                    r.bid_amt::float / NULLIF(r.estimated_price, 0) * 100
                        AS ratio,
                    c.openg_date,
                    LEFT(
                        REGEXP_REPLACE(c.openg_date, '[^0-9]', '', 'g'), 6
                    ) AS openg_month,
                    c.ntce_org, c.demand_org, c.demand_org_area,
                    c.jurisdiction, c.bid_method, c.win_method,
                    c.company_area,
                    -- 가격대 세그먼트 (CONSTRUCTION 기준)
                    -- ⚠️ SPECIALTY 혼입 가능 (work_type 미분류)
                    CASE
                        WHEN r.presume_price < 200000000  THEN 'T5'
                        WHEN r.presume_price < 300000000  THEN 'T4'
                        WHEN r.presume_price < 1000000000 THEN 'T3'
                        WHEN r.presume_price < 5000000000 THEN 'T2A'
                        ELSE 'T1'
                    END AS price_seg,
                    -- 경쟁강도 세그먼트
                    CASE
                        WHEN r.bidder_cnt <= 9   THEN 'C01_09'
                        WHEN r.bidder_cnt <= 29  THEN 'C10_29'
                        WHEN r.bidder_cnt <= 49  THEN 'C30_49'
                        WHEN r.bidder_cnt <= 99  THEN 'C50_99'
                        WHEN r.bidder_cnt <= 199 THEN 'C100_199'
                        ELSE 'C200+'
                    END AS comp_seg
                FROM g2b_bidresult r
                LEFT JOIN (
                    SELECT DISTINCT ON (bid_ntce_no, bid_ntce_ord)
                        bid_ntce_no, bid_ntce_ord,
                        openg_date, ntce_org, demand_org, demand_org_area,
                        jurisdiction, bid_method, win_method, company_area
                    FROM g2b_bidcontract
                    ORDER BY bid_ntce_no, bid_ntce_ord,
                             REGEXP_REPLACE(openg_date, '[^0-9]', '', 'g')
                             DESC
                ) c ON r.bid_ntce_no = c.bid_ntce_no
                       AND r.bid_ntce_ord = c.bid_ntce_ord
                WHERE r.presume_price > 0
                  AND r.presume_price < 10000000000
                  AND r.estimated_price > 0
                  AND r.bid_amt > 0
                  AND r.success_lowest_rate > 0
                  AND r.bid_amt::float / NULLIF(r.estimated_price, 0) * 100
                      BETWEEN 70 AND 110
            """)

            for cols in [
                "bid_ntce_no, bid_ntce_ord", "presume_price",
                "openg_month", "company_bizno", "openg_rank",
                "price_seg", "comp_seg", "jurisdiction",
            ]:
                cur.execute(f"CREATE INDEX ON _cross_base ({cols})")

            cur.execute("SELECT COUNT(*) FROM _cross_base")
            cnt = cur.fetchone()[0]

        elapsed = (datetime.now() - t0).total_seconds()
        self.stdout.write(f"  _cross_base: {cnt:,d}행 ({elapsed:.1f}초)")
        self.stdout.write(
            "  ⚠️ CONSTRUCTION 경계 가정, SPECIALTY 혼입 가능"
        )
        return cnt

    def _drop_cross_base(self):
        with connection.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS _cross_base")

    # ──────────────────────────────────────────────
    # M1: 표본편향 감사 (Layer C 전제 검증)
    # ──────────────────────────────────────────────

    def _m1_sampling_bias(self) -> dict:
        """API 477건이 시장 전체를 대표하는가?"""
        with connection.cursor() as cur:
            # 시장 분포 (공고 단위 DISTINCT)
            cur.execute("""
                SELECT price_seg, comp_seg,
                    COUNT(DISTINCT (bid_ntce_no, bid_ntce_ord)) AS ntce_cnt
                FROM _cross_base
                GROUP BY price_seg, comp_seg
                ORDER BY price_seg, comp_seg
            """)
            cols = [c[0] for c in cur.description]
            market = [dict(zip(cols, r)) for r in cur.fetchall()]

            # API 분포 (공고 단위 DISTINCT)
            cur.execute("""
                SELECT cb.price_seg, cb.comp_seg,
                    COUNT(DISTINCT (cb.bid_ntce_no, cb.bid_ntce_ord))
                        AS ntce_cnt
                FROM _cross_base cb
                INNER JOIN g2b_bidapicollectionlog cl
                    ON cb.bid_ntce_no = cl.bid_ntce_no
                    AND cb.bid_ntce_ord = cl.bid_ntce_ord
                WHERE cl.a_value_status = 'ok'
                  AND cl.prelim_status = 'ok'
                GROUP BY cb.price_seg, cb.comp_seg
                ORDER BY cb.price_seg, cb.comp_seg
            """)
            cols = [c[0] for c in cur.description]
            api = [dict(zip(cols, r)) for r in cur.fetchall()]

        market_total = sum(r["ntce_cnt"] for r in market)
        api_total = sum(r["ntce_cnt"] for r in api)

        if api_total < 100:
            self.stderr.write(
                f"  ⚠️ API 건수 {api_total} < 100 — 표본 부족, M7 skip 권고"
            )

        for r in market:
            r["pct"] = r["ntce_cnt"] / market_total if market_total else 0
        for r in api:
            r["pct"] = r["ntce_cnt"] / api_total if api_total else 0

        # PSI + JS divergence
        market_dict = {
            (r["price_seg"], r["comp_seg"]): r["pct"] for r in market
        }
        api_dict = {
            (r["price_seg"], r["comp_seg"]): r["pct"] for r in api
        }
        all_keys = set(market_dict) | set(api_dict)
        eps = 1e-6
        psi = 0.0
        js_sum = 0.0
        overrep, underrep = [], []

        for k in all_keys:
            p = max(market_dict.get(k, eps), eps)
            q = max(api_dict.get(k, eps), eps)
            psi += (q - p) * math.log(q / p)
            m_val = 0.5 * (p + q)
            if m_val > 0:
                js_sum += 0.5 * (
                    p * math.log(p / m_val) + q * math.log(q / m_val)
                )
            seg_id = f"{k[0]}_{k[1]}"
            if q > p * 2 and q > 0.01:
                overrep.append({
                    "segment": seg_id,
                    "market_pct": round(p, 4),
                    "api_pct": round(q, 4),
                })
            if p > q * 2 and p > 0.01:
                underrep.append({
                    "segment": seg_id,
                    "market_pct": round(p, 4),
                    "api_pct": round(q, 4),
                })

        if psi < 0.1:
            severity = "stable"
        elif psi < 0.25:
            severity = "moderate"
        else:
            severity = "severe"

        # 샘플링 목표
        sampling_targets = []
        for r in market:
            k = (r["price_seg"], r["comp_seg"])
            api_cnt = next(
                (a["ntce_cnt"] for a in api
                 if a["price_seg"] == r["price_seg"]
                 and a["comp_seg"] == r["comp_seg"]),
                0,
            )
            target = max(30, int(r["pct"] * api_total * 2))
            if api_cnt < target:
                sampling_targets.append({
                    "price_seg": r["price_seg"],
                    "comp_seg": r["comp_seg"],
                    "current": api_cnt,
                    "target": target,
                })

        result = {
            "meta": {"module": "M1", "description": "표본편향 감사"},
            "market_distribution": market,
            "api_distribution": api,
            "market_total": market_total,
            "api_total": api_total,
            "psi": round(psi, 4),
            "js_divergence": round(js_sum, 4),
            "bias_severity": severity,
            "overrepresented": overrep,
            "underrepresented": underrep,
            "sampling_targets": sorted(
                sampling_targets,
                key=lambda x: x["target"] - x["current"],
                reverse=True,
            )[:10],
        }

        self._print_m1(result)
        return result

    def _print_m1(self, data: dict):
        self.stdout.write(f"\n  시장 공고: {data['market_total']:,d}건")
        self.stdout.write(f"  API 공고:  {data['api_total']:,d}건")
        self.stdout.write(
            f"  PSI: {data['psi']:.4f} ({data['bias_severity']})"
        )
        self.stdout.write(f"  JS divergence: {data['js_divergence']:.4f}")
        if data["overrepresented"]:
            self.stdout.write("  과대표본:")
            for r in data["overrepresented"][:5]:
                self.stdout.write(
                    f"    {r['segment']}: "
                    f"시장 {r['market_pct']:.1%} → API {r['api_pct']:.1%}"
                )
        if data["underrepresented"]:
            self.stdout.write("  과소표본:")
            for r in data["underrepresented"][:5]:
                self.stdout.write(
                    f"    {r['segment']}: "
                    f"시장 {r['market_pct']:.1%} → API {r['api_pct']:.1%}"
                )

    # ──────────────────────────────────────────────
    # M2: 조건부 승률면 (Layer A 핵심)
    # ──────────────────────────────────────────────

    def _m2_winrate_surface(self) -> dict:
        """어떤 조건에서 어느 비율대가 유리한가?"""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT price_seg, comp_seg,
                    COUNT(*) AS n,
                    COUNT(DISTINCT (bid_ntce_no, bid_ntce_ord)) AS ntce_cnt,
                    AVG(CASE WHEN openg_rank = '1' THEN ratio END)
                        AS win_avg,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (
                        ORDER BY CASE WHEN openg_rank = '1' THEN ratio END
                    ) AS win_median,
                    STDDEV(CASE WHEN openg_rank = '1' THEN ratio END)
                        AS win_std,
                    PERCENTILE_CONT(0.1) WITHIN GROUP (
                        ORDER BY CASE WHEN openg_rank = '1' THEN ratio END
                    ) AS win_p10,
                    AVG(ratio) AS all_avg,
                    STDDEV(ratio) AS all_std
                FROM _cross_base
                GROUP BY price_seg, comp_seg
                ORDER BY price_seg, comp_seg
            """)
            cols = [c[0] for c in cur.description]
            surface_raw = [dict(zip(cols, r)) for r in cur.fetchall()]

            # jurisdiction별
            cur.execute("""
                SELECT price_seg, jurisdiction,
                    COUNT(DISTINCT (bid_ntce_no, bid_ntce_ord)) AS ntce_cnt,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (
                        ORDER BY CASE WHEN openg_rank = '1'
                                      THEN ratio END
                    ) AS win_median
                FROM _cross_base
                WHERE jurisdiction != ''
                GROUP BY price_seg, jurisdiction
                HAVING COUNT(DISTINCT (bid_ntce_no, bid_ntce_ord)) >= 100
                ORDER BY price_seg, jurisdiction
            """)
            cols = [c[0] for c in cur.description]
            by_jurisdiction = [dict(zip(cols, r)) for r in cur.fetchall()]

        # 셀당 300건 미달 표시
        surface = []
        merged_count = 0
        for row in surface_raw:
            row["merged_from"] = None
            if (row["ntce_cnt"] or 0) < 300:
                row["merged_from"] = "low_sample"
                merged_count += 1
            surface.append(row)

        total_ntce = sum(r["ntce_cnt"] or 0 for r in surface)

        result = {
            "meta": {"module": "M2", "description": "조건부 승률면"},
            "surface": surface,
            "by_jurisdiction": by_jurisdiction,
            "cell_count": len(surface),
            "merged_count": merged_count,
            "total_ntce": total_ntce,
        }

        self._print_m2(result)
        return result

    def _print_m2(self, data: dict):
        self.stdout.write(
            f"\n  셀 수: {data['cell_count']} "
            f"(low_sample: {data['merged_count']})"
        )
        self.stdout.write(f"  총 공고: {data['total_ntce']:,d}")
        self.stdout.write(
            f"\n  {'가격대':<6s} {'경쟁':<9s} {'공고수':>8s} "
            f"{'1위평균':>8s} {'1위중앙':>8s} {'1위σ':>6s} {'1위P10':>7s}"
        )
        for r in data["surface"]:
            flag = " *" if r["merged_from"] else ""
            self.stdout.write(
                f"  {r['price_seg']:<6s} {r['comp_seg']:<9s} "
                f"{(r['ntce_cnt'] or 0):>8,d} "
                f"{(r['win_avg'] or 0):>8.2f} "
                f"{(r['win_median'] or 0):>8.2f} "
                f"{(r['win_std'] or 0):>6.2f} "
                f"{(r['win_p10'] or 0):>7.2f}{flag}"
            )

    # ──────────────────────────────────────────────
    # M3: 피크/숫자 편향 (Layer B)
    # ──────────────────────────────────────────────

    def _m3_ratio_peaks(self) -> dict:
        """특정 소수점 비율에 과밀이 있는가?"""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    FLOOR(ratio * 100) / 100 AS bin,
                    price_seg,
                    COUNT(*) AS cnt,
                    COUNT(CASE WHEN openg_rank = '1' THEN 1 END)
                        AS win_cnt
                FROM _cross_base
                WHERE ratio BETWEEN 86 AND 94
                GROUP BY bin, price_seg
                ORDER BY bin, price_seg
            """)
            cols = [c[0] for c in cur.description]
            bins = [dict(zip(cols, r)) for r in cur.fetchall()]

        # 전체 bin 합산 (price_seg 무시)
        bin_totals: dict[float, int] = {}
        for b in bins:
            bv = float(b["bin"])
            bin_totals[bv] = bin_totals.get(bv, 0) + b["cnt"]

        counts = list(bin_totals.values())
        if len(counts) >= 2:
            mean_cnt = statistics.mean(counts)
            std_cnt = statistics.stdev(counts)
        else:
            mean_cnt = sum(counts) / max(len(counts), 1)
            std_cnt = 1.0

        # 유의미 피크 (z > 3)
        peaks = []
        for bv, cnt in sorted(bin_totals.items()):
            z = (cnt - mean_cnt) / std_cnt if std_cnt > 0 else 0
            if z > 3:
                excess_pct = (
                    (cnt - mean_cnt) / mean_cnt * 100 if mean_cnt > 0 else 0
                )
                frac = bv % 1.0
                interp = (
                    "정수 편향"
                    if abs(frac) < 0.01 or abs(frac - 0.5) < 0.01
                    else "밀집 구간"
                )
                peaks.append({
                    "bin": round(bv, 2),
                    "z_score": round(z, 2),
                    "excess_pct": round(excess_pct, 1),
                    "interpretation": interp,
                })

        # bin별 z_score 첨부
        for b in bins:
            bv = float(b["bin"])
            cnt = bin_totals.get(bv, 0)
            b["z_score"] = (
                round((cnt - mean_cnt) / std_cnt, 2) if std_cnt > 0 else 0
            )

        result = {
            "meta": {"module": "M3", "description": "피크/숫자 편향"},
            "bins": bins,
            "peaks": peaks,
            "total_bins": len(bin_totals),
            "significant_peaks": len(peaks),
            "peak_ratio_to_baseline": round(
                max(bin_totals.values()) / mean_cnt
                if mean_cnt > 0 and bin_totals
                else 0,
                2,
            ),
        }

        self._print_m3(result)
        return result

    def _print_m3(self, data: dict):
        self.stdout.write(
            f"\n  총 bin: {data['total_bins']}, "
            f"유의미 피크(z>3): {data['significant_peaks']}"
        )
        self.stdout.write(
            f"  피크/기준선 비율: {data['peak_ratio_to_baseline']:.2f}x"
        )
        if data["peaks"]:
            self.stdout.write(
                f"\n  {'비율(%)':>8s} {'z-score':>8s} "
                f"{'초과%':>7s} {'해석'}"
            )
            for p in data["peaks"][:15]:
                self.stdout.write(
                    f"  {p['bin']:>8.2f} {p['z_score']:>8.2f} "
                    f"{p['excess_pct']:>7.1f}% {p['interpretation']}"
                )

    # ──────────────────────────────────────────────
    # M4: 경쟁압력 지도 (Layer A)
    # ──────────────────────────────────────────────

    def _m4_competition_pressure(self) -> dict:
        """경쟁자 수 증가에 따른 최적 구간 이동."""
        with connection.cursor() as cur:
            cur.execute("""
                WITH ranked AS (
                    SELECT *,
                        NTILE(10) OVER (ORDER BY bidder_cnt)
                            AS bidder_decile
                    FROM _cross_base
                    WHERE openg_rank IN ('1', '2')
                )
                SELECT bidder_decile,
                    MIN(bidder_cnt) AS min_bidders,
                    MAX(bidder_cnt) AS max_bidders,
                    COUNT(CASE WHEN openg_rank = '1' THEN 1 END)
                        AS r1_cnt,
                    AVG(CASE WHEN openg_rank = '1' THEN ratio END)
                        AS r1_avg,
                    AVG(CASE WHEN openg_rank = '2' THEN ratio END)
                        AS r2_avg,
                    AVG(CASE WHEN openg_rank = '1' THEN ratio END) -
                        AVG(CASE WHEN openg_rank = '2' THEN ratio END)
                        AS gap_1_2,
                    PERCENTILE_CONT(0.1) WITHIN GROUP (
                        ORDER BY CASE WHEN openg_rank = '1'
                                      THEN ratio END
                    ) AS r1_p10
                FROM ranked
                GROUP BY bidder_decile
                ORDER BY bidder_decile
            """)
            cols = [c[0] for c in cur.description]
            deciles = [dict(zip(cols, r)) for r in cur.fetchall()]

        # 수렴점 (gap < 0.05)
        convergence = None
        for d in deciles:
            gap = d.get("gap_1_2")
            if gap is not None and abs(gap) < 0.05:
                convergence = {
                    "decile": d["bidder_decile"],
                    "gap": round(gap, 3),
                    "description": (
                        f"{d['min_bidders']}~{d['max_bidders']}명부터 "
                        f"1-2순위 gap 수렴"
                    ),
                }
                break

        tail_risk = None
        if deciles:
            last = deciles[-1]
            if last.get("r1_p10") is not None:
                tail_risk = {
                    "decile": last["bidder_decile"],
                    "r1_p10": round(float(last["r1_p10"]), 2),
                }

        result = {
            "meta": {"module": "M4", "description": "경쟁압력 지도"},
            "deciles": deciles,
            "convergence_point": convergence,
            "tail_risk_threshold": tail_risk,
        }

        self._print_m4(result)
        return result

    def _print_m4(self, data: dict):
        self.stdout.write(
            f"\n  {'분위':>4s} {'경쟁(명)':>12s} {'1위건수':>8s} "
            f"{'1위평균':>8s} {'2위평균':>8s} {'gap':>6s} {'1위P10':>7s}"
        )
        for d in data["deciles"]:
            self.stdout.write(
                f"  {d['bidder_decile']:>4d} "
                f"{d['min_bidders']:>5d}~{d['max_bidders']:<5d} "
                f"{d['r1_cnt']:>8,d} "
                f"{(d['r1_avg'] or 0):>8.2f} "
                f"{(d['r2_avg'] or 0):>8.2f} "
                f"{(d['gap_1_2'] or 0):>6.3f} "
                f"{(d['r1_p10'] or 0):>7.2f}"
            )
        if data["convergence_point"]:
            cp = data["convergence_point"]
            self.stdout.write(
                f"\n  수렴점: decile {cp['decile']} "
                f"({cp['description']})"
            )

    # ──────────────────────────────────────────────
    # M5: 업체 아키타입 (Layer B)
    # ──────────────────────────────────────────────

    def _m5_company_archetypes(self) -> dict:
        """업체 고정형/적응형/분산형 분류."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT company_bizno,
                    COUNT(*) AS bid_cnt,
                    COUNT(DISTINCT (bid_ntce_no, bid_ntce_ord))
                        AS ntce_cnt,
                    AVG(ratio) AS avg_ratio,
                    STDDEV(ratio) AS std_ratio,
                    MAX(ratio) - MIN(ratio) AS range_ratio,
                    COUNT(DISTINCT price_seg) AS n_segments
                FROM _cross_base
                GROUP BY company_bizno
                HAVING COUNT(*) >= 10
            """)
            cols = [c[0] for c in cur.description]
            companies = [dict(zip(cols, r)) for r in cur.fetchall()]

            cur.execute(
                "SELECT COUNT(DISTINCT company_bizno) FROM _cross_base"
            )
            total_companies = cur.fetchone()[0]

        # 분류
        buckets: dict[str, list] = {
            "ultra_fixed": [], "fixed": [],
            "adaptive": [], "dispersed": [],
        }
        for c in companies:
            std = float(c["std_ratio"] or 0)
            rng = float(c["range_ratio"] or 0)
            if std < 0.3 and rng < 1.0:
                c["archetype"] = "ultra_fixed"
            elif std < 1.0:
                c["archetype"] = "fixed"
            elif std < 2.0:
                c["archetype"] = "adaptive"
            else:
                c["archetype"] = "dispersed"
            buckets[c["archetype"]].append(c)

        qualified = len(companies)
        summary: dict[str, Any] = {}
        for atype, items in buckets.items():
            cnt = len(items)
            summary[atype] = {
                "count": cnt,
                "pct": round(cnt / qualified * 100, 1) if qualified else 0,
                "avg_ratio": (
                    round(
                        statistics.mean(
                            float(c["avg_ratio"]) for c in items
                        ), 2,
                    )
                    if items else 0
                ),
                "avg_std": (
                    round(
                        statistics.mean(
                            float(c["std_ratio"] or 0) for c in items
                        ), 2,
                    )
                    if items else 0
                ),
            }

        # 세그먼트별 분포 (SQL)
        with connection.cursor() as cur:
            cur.execute("""
                WITH comp AS (
                    SELECT company_bizno,
                        MODE() WITHIN GROUP (ORDER BY price_seg)
                            AS main_seg,
                        STDDEV(ratio) AS std_ratio,
                        MAX(ratio) - MIN(ratio) AS range_ratio
                    FROM _cross_base
                    GROUP BY company_bizno
                    HAVING COUNT(*) >= 10
                )
                SELECT main_seg AS price_seg,
                    COUNT(*) AS total,
                    COUNT(CASE WHEN std_ratio < 0.3
                               AND range_ratio < 1.0 THEN 1 END)
                        AS ultra_fixed,
                    COUNT(CASE WHEN std_ratio >= 0.3
                               AND std_ratio < 1.0 THEN 1 END)
                        AS fixed,
                    COUNT(CASE WHEN std_ratio >= 1.0
                               AND std_ratio < 2.0 THEN 1 END)
                        AS adaptive,
                    COUNT(CASE WHEN std_ratio >= 2.0 THEN 1 END)
                        AS dispersed
                FROM comp
                GROUP BY main_seg
                ORDER BY main_seg
            """)
            cols = [c[0] for c in cur.description]
            by_segment_raw = [dict(zip(cols, r)) for r in cur.fetchall()]

        by_segment = []
        for row in by_segment_raw:
            total = row["total"] or 1
            by_segment.append({
                "price_seg": row["price_seg"],
                "ultra_fixed_pct": round(
                    row["ultra_fixed"] / total * 100, 1
                ),
                "fixed_pct": round(row["fixed"] / total * 100, 1),
                "adaptive_pct": round(row["adaptive"] / total * 100, 1),
                "dispersed_pct": round(row["dispersed"] / total * 100, 1),
            })

        result = {
            "meta": {"module": "M5", "description": "업체 아키타입"},
            "summary": {
                "total_companies": total_companies,
                "qualified_companies": qualified,
                **summary,
            },
            "by_segment": by_segment,
        }

        self._print_m5(result)
        return result

    def _print_m5(self, data: dict):
        s = data["summary"]
        self.stdout.write(f"\n  전체 업체: {s['total_companies']:,d}")
        self.stdout.write(
            f"  분류 대상 (10건+): {s['qualified_companies']:,d}"
        )
        for atype in ["ultra_fixed", "fixed", "adaptive", "dispersed"]:
            a = s[atype]
            self.stdout.write(
                f"  {atype:<14s}: {a['count']:>6,d} ({a['pct']:>5.1f}%) "
                f"평균비율 {a['avg_ratio']:.2f} σ={a['avg_std']:.2f}"
            )

    # ──────────────────────────────────────────────
    # M6: 제도/시계열 변화 (Layer A+B)
    # ──────────────────────────────────────────────

    def _m6_regime_shift(self) -> dict:
        """시점 변화가 전략을 바꿨는가?"""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT openg_month, price_seg,
                    COUNT(DISTINCT (bid_ntce_no, bid_ntce_ord))
                        AS ntce_cnt,
                    AVG(bidder_cnt) AS avg_bidders,
                    AVG(CASE WHEN openg_rank = '1' THEN ratio END)
                        AS win_avg,
                    STDDEV(CASE WHEN openg_rank = '1' THEN ratio END)
                        AS win_std,
                    COUNT(CASE WHEN openg_rank = '1' THEN 1 END)
                        AS win_cnt
                FROM _cross_base
                WHERE openg_month IS NOT NULL
                  AND openg_month >= '202402'
                GROUP BY openg_month, price_seg
                HAVING COUNT(*) >= 100
                ORDER BY openg_month, price_seg
            """)
            cols = [c[0] for c in cur.description]
            monthly = [dict(zip(cols, r)) for r in cur.fetchall()]

        # 변화점 감지: rolling z-test (3개월 recent vs 이전 6개월)
        changepoints = []
        seg_months: dict[str, list] = {}
        for row in monthly:
            seg = row["price_seg"]
            if seg not in seg_months:
                seg_months[seg] = []
            seg_months[seg].append(row)

        for seg, rows in seg_months.items():
            rows.sort(key=lambda x: x["openg_month"])
            if len(rows) < 9:
                continue
            for i in range(6, len(rows) - 2):
                prior = rows[max(0, i - 6):i]
                recent = rows[i:i + 3]

                prior_vals = [
                    float(r["win_avg"]) for r in prior
                    if r["win_avg"] is not None
                ]
                recent_vals = [
                    float(r["win_avg"]) for r in recent
                    if r["win_avg"] is not None
                ]
                if len(prior_vals) < 3 or len(recent_vals) < 2:
                    continue

                mean_prior = statistics.mean(prior_vals)
                mean_recent = statistics.mean(recent_vals)
                var_prior = (
                    statistics.variance(prior_vals)
                    if len(prior_vals) > 1 else 0.01
                )
                var_recent = (
                    statistics.variance(recent_vals)
                    if len(recent_vals) > 1 else 0.01
                )

                denom = math.sqrt(
                    var_prior / len(prior_vals)
                    + var_recent / len(recent_vals)
                )
                if denom < 1e-6:
                    continue

                z = (mean_recent - mean_prior) / denom
                if abs(z) >= 2.0:
                    changepoints.append({
                        "month": rows[i]["openg_month"],
                        "price_seg": seg,
                        "z_score": round(z, 2),
                        "direction": "up" if z > 0 else "down",
                        "before_avg": round(mean_prior, 2),
                        "after_avg": round(mean_recent, 2),
                        "delta": round(mean_recent - mean_prior, 2),
                        "possible_cause": self._guess_cause(
                            rows[i]["openg_month"]
                        ),
                    })

        cp_months = set(cp["month"] for cp in changepoints)
        all_months = set(r["openg_month"] for r in monthly)

        result = {
            "meta": {"module": "M6", "description": "제도/시계열 변화"},
            "monthly": monthly,
            "changepoints": changepoints,
            "regime_count": len(cp_months) + 1,
            "stable_months": max(len(all_months) - len(cp_months), 0),
        }

        self._print_m6(result)
        return result

    @staticmethod
    def _guess_cause(month: str) -> str:
        if month >= "202601":
            return "낙찰하한율 +2%p 상향 시행 (2026.1.30)"
        if month >= "202512":
            return "조달청지침 #9269 시행 (2025.12.1)"
        return ""

    def _print_m6(self, data: dict):
        self.stdout.write(f"\n  월별 데이터: {len(data['monthly'])}건")
        self.stdout.write(f"  변화점: {len(data['changepoints'])}건")
        self.stdout.write(f"  체제 수: {data['regime_count']}")
        if data["changepoints"]:
            self.stdout.write(
                f"\n  {'월':>8s} {'가격대':<6s} {'z':>6s} {'방향':<5s} "
                f"{'전':>7s} {'후':>7s} {'δ':>6s}"
            )
            for cp in data["changepoints"]:
                self.stdout.write(
                    f"  {cp['month']:>8s} {cp['price_seg']:<6s} "
                    f"{cp['z_score']:>6.2f} {cp['direction']:<5s} "
                    f"{cp['before_avg']:>7.2f} {cp['after_avg']:>7.2f} "
                    f"{cp['delta']:>+6.2f}"
                )
                if cp["possible_cause"]:
                    self.stdout.write(
                        f"         → {cp['possible_cause']}"
                    )

    # ──────────────────────────────────────────────
    # M7: 시나리오 민감도 (Layer C)
    # ──────────────────────────────────────────────

    def _m7_scenario_sensitivity(self) -> dict:
        """세그먼트별 C(15,4) 시나리오 민감도."""
        from g2b.services.bid_engine import (
            TABLE_PARAMS_MAP,
            AValueItems,
            TableType,
            WorkType,
            calculate_a_value,
            select_table,
        )
        from g2b.services.optimal_bid import (
            OptimalBidInput,
            find_optimal_bid,
            generate_scenarios,
        )

        a_values_map = self._load_a_values()
        prelim_map = self._load_prelim_prices()
        rank1_map = self._load_rank1_with_segments()

        common_keys = set(a_values_map) & set(prelim_map) & set(rank1_map)
        self.stdout.write(
            f"  대상: {len(common_keys)}건 (A값∩복수예비∩1순위)"
        )

        if len(common_keys) < 100:
            self.stderr.write(
                f"  ⚠️ 대상 {len(common_keys)} < 100 — 시나리오 분석 부족"
            )

        records = []
        skipped = 0
        processed = 0

        for key in sorted(common_keys):
            a_val = a_values_map[key]
            prelim_prices = prelim_map[key]
            r1 = rank1_map[key]
            presume = r1["presume_price"]

            if presume >= 100 * UNIT_EOUK or presume <= 0:
                skipped += 1
                continue

            try:
                table_type = select_table(presume, WorkType.CONSTRUCTION)
                if table_type == TableType.OUT_OF_SCOPE:
                    skipped += 1
                    continue

                inp = OptimalBidInput(
                    preliminary_prices=prelim_prices,
                    a_value=a_val,
                    table_type=table_type,
                    presume_price=presume,
                )
                opt = find_optimal_bid(inp)

                scenarios = generate_scenarios(prelim_prices)
                params = TABLE_PARAMS_MAP[table_type]
                max_s = float(params.max_score)
                coeff = float(params.coeff)
                fixed_ratio = float(params.fixed_ratio)
                fixed_score = float(params.fixed_score)

                scores = []
                for est in scenarios:
                    s = self._calc_score_float(
                        opt.recommended_bid, est, a_val,
                        max_s, coeff, fixed_ratio, fixed_score,
                    )
                    scores.append(s)

                scores.sort()
                n_sc = len(scores)
                p10_idx = max(0, int(n_sc * 0.1) - 1)
                cvar_n = max(1, int(n_sc * 0.1))

                records.append({
                    "bid_ntce_no": key[0],
                    "bid_ntce_ord": key[1],
                    "price_seg": r1["price_seg"],
                    "comp_seg": r1["comp_seg"],
                    "expected_score": round(opt.expected_score, 2),
                    "std_score": (
                        round(statistics.stdev(scores), 2)
                        if len(scores) > 1 else 0
                    ),
                    "p10_score": round(scores[p10_idx], 2),
                    "cvar_10": round(
                        statistics.mean(scores[:cvar_n]), 2
                    ),
                    "min_score": round(scores[0], 2),
                    "max_score": round(scores[-1], 2),
                    "n_scenarios": n_sc,
                })

                processed += 1
                if processed % 50 == 0:
                    self.stdout.write(
                        f"  ... {processed}/{len(common_keys)} 처리"
                    )

            except Exception:
                skipped += 1

        # 세그먼트별 집계
        seg_agg: dict[str, list] = {}
        for rec in records:
            seg_key = f"{rec['price_seg']}_{rec['comp_seg']}"
            if seg_key not in seg_agg:
                seg_agg[seg_key] = []
            seg_agg[seg_key].append(rec)

        by_segment = []
        for seg_key, items in sorted(seg_agg.items()):
            parts = seg_key.split("_", 1)
            mean_exp = statistics.mean(
                r["expected_score"] for r in items
            )
            by_segment.append({
                "price_seg": parts[0],
                "comp_seg": parts[1] if len(parts) > 1 else "",
                "count": len(items),
                "mean_expected": round(mean_exp, 2),
                "std_expected": (
                    round(
                        statistics.stdev(
                            r["expected_score"] for r in items
                        ), 2,
                    )
                    if len(items) > 1 else 0
                ),
                "mean_p10": round(
                    statistics.mean(r["p10_score"] for r in items), 2
                ),
                "mean_cvar10": round(
                    statistics.mean(r["cvar_10"] for r in items), 2
                ),
                "mean_min_score": round(
                    statistics.mean(r["min_score"] for r in items), 2
                ),
                "mean_max_score": round(
                    statistics.mean(r["max_score"] for r in items), 2
                ),
                "sensitivity": round(
                    statistics.mean(r["std_score"] for r in items)
                    / max(mean_exp, 1),
                    4,
                ),
            })

        result = {
            "meta": {"module": "M7", "description": "시나리오 민감도"},
            "total_processed": len(records),
            "skipped": skipped,
            "by_segment": by_segment,
            "records": records,
        }

        self._print_m7(result)
        return result

    @staticmethod
    def _calc_score_float(
        bid: int, est: int, a: int,
        max_s: float, coeff: float,
        fixed_ratio: float, fixed_score: float,
    ) -> float:
        """float 기반 가격점수 (optimal_bid._score_fast 로직 복제)."""
        if a >= est:
            return 2.0
        ratio_raw = (bid - a) / (est - a)
        m = 10 ** 4
        ratio = int(ratio_raw * m + 0.5) / m
        if bid <= est and ratio >= fixed_ratio:
            return fixed_score
        score = max_s - coeff * abs(90.0 - ratio * 100.0)
        return max(score, 2.0)

    def _load_a_values(self) -> dict:
        """BidApiAValue → {(ntce_no, ntce_ord): a_value_int}."""
        from g2b.services.bid_engine import AValueItems, calculate_a_value

        with connection.cursor() as cur:
            cur.execute("""
                SELECT bid_ntce_no, bid_ntce_ord,
                    national_pension, health_insurance,
                    retirement_mutual_aid, long_term_care,
                    occupational_safety, safety_management,
                    quality_management
                FROM g2b_bidapiavalue
            """)
            rows = cur.fetchall()

        result = {}
        for row in rows:
            items = AValueItems(
                national_pension=row[2],
                health_insurance=row[3],
                retirement_mutual_aid=row[4],
                long_term_care=row[5],
                occupational_safety=row[6],
                safety_management=row[7],
                quality_management=row[8],
            )
            result[(row[0], row[1])] = calculate_a_value(items)
        return result

    def _load_prelim_prices(self) -> dict:
        """BidApiPrelimPrice → {(ntce_no, ntce_ord): [price, ...]}."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT bid_ntce_no, bid_ntce_ord, basis_planned_price
                FROM g2b_bidapiprelimprice
                WHERE basis_planned_price > 0
                ORDER BY bid_ntce_no, bid_ntce_ord, sequence_no
            """)
            rows = cur.fetchall()

        groups: dict[tuple, list] = {}
        for ntce_no, ntce_ord, price in rows:
            key = (ntce_no, ntce_ord)
            if key not in groups:
                groups[key] = []
            groups[key].append(price)

        # C(n,4) 필요: 최소 4개
        return {k: v for k, v in groups.items() if len(v) >= 4}

    def _load_rank1_with_segments(self) -> dict:
        """API 대상 공고의 1순위 결과 + 세그먼트."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT cb.bid_ntce_no, cb.bid_ntce_ord,
                    cb.presume_price, cb.estimated_price,
                    cb.bid_amt, cb.bidder_cnt,
                    cb.price_seg, cb.comp_seg
                FROM _cross_base cb
                INNER JOIN g2b_bidapicollectionlog cl
                    ON cb.bid_ntce_no = cl.bid_ntce_no
                    AND cb.bid_ntce_ord = cl.bid_ntce_ord
                WHERE cl.a_value_status = 'ok'
                  AND cl.prelim_status = 'ok'
                  AND cb.openg_rank = '1'
            """)
            rows = cur.fetchall()

        result = {}
        for row in rows:
            key = (row[0], row[1])
            result[key] = {
                "presume_price": row[2],
                "estimated_price": row[3],
                "bid_amt": row[4],
                "bidder_cnt": row[5],
                "price_seg": row[6],
                "comp_seg": row[7],
            }
        return result

    def _print_m7(self, data: dict):
        self.stdout.write(
            f"\n  처리: {data['total_processed']}건 "
            f"(skip: {data['skipped']})"
        )
        if data["by_segment"]:
            self.stdout.write(
                f"\n  {'가격대':<5s} {'경쟁':<9s} {'건수':>5s} "
                f"{'기대':>6s} {'P10':>6s} {'CVaR':>6s} {'민감도':>7s}"
            )
            for s in data["by_segment"]:
                self.stdout.write(
                    f"  {s['price_seg']:<5s} {s['comp_seg']:<9s} "
                    f"{s['count']:>5d} {s['mean_expected']:>6.1f} "
                    f"{s['mean_p10']:>6.1f} {s['mean_cvar10']:>6.1f} "
                    f"{s['sensitivity']:>7.4f}"
                )

    # ──────────────────────────────────────────────
    # M8: 정책 추출 (M2~M7 결과 종합)
    # ──────────────────────────────────────────────

    def _m8_policy_extraction(self, results: dict) -> dict:
        """M2~M7 결과를 종합하여 세그먼트별 정책 테이블 생성."""
        m2 = results.get("M2", {})
        m3 = results.get("M3", {})
        m4 = results.get("M4", {})
        m6 = results.get("M6", {})
        m7 = results.get("M7", {})
        m1 = results.get("M1", {})

        surface = m2.get("surface", [])
        if not surface:
            self.stderr.write("  ⚠️ M2 결과 필요 — M2 먼저 실행하세요")
            return {"error": "M2 결과 필요 — M2 먼저 실행하세요"}

        # M3: 피크 비율 set
        peak_bins = set()
        for p in m3.get("peaks", []):
            peak_bins.add(round(p["bin"], 2))

        # M4: 수렴점
        convergence = m4.get("convergence_point")

        # M6: 변화점
        changepoints = {
            (cp["price_seg"], cp["month"]): cp
            for cp in m6.get("changepoints", [])
        }

        # M7: 세그먼트별 민감도
        sensitivity_map = {}
        for s in m7.get("by_segment", []):
            seg_key = f"{s['price_seg']}_{s['comp_seg']}"
            sensitivity_map[seg_key] = s

        # M1: API 분포
        api_cnt_map = {}
        for a in m1.get("api_distribution", []):
            seg_key = f"{a['price_seg']}_{a['comp_seg']}"
            api_cnt_map[seg_key] = a["ntce_cnt"]

        # M6: 월별 안정성 계산용
        monthly_by_seg: dict[str, list] = {}
        for row in m6.get("monthly", []):
            seg = row["price_seg"]
            if seg not in monthly_by_seg:
                monthly_by_seg[seg] = []
            monthly_by_seg[seg].append(row)

        policy = []
        rules = []
        rule_id = 0

        for cell in surface:
            price_seg = cell["price_seg"]
            comp_seg = cell["comp_seg"]
            seg_id = f"{price_seg}_{comp_seg}"

            win_median = float(cell.get("win_median") or 0)
            win_std = float(cell.get("win_std") or 0)
            ntce_cnt = cell.get("ntce_cnt") or 0

            if win_median == 0:
                continue

            # 마진 (최소 0.5%p)
            margin = max(0.5, win_std * 0.5)

            # M4 경쟁 보정: 고경쟁 셀 margin 축소
            if convergence and comp_seg in ("C100_199", "C200+"):
                margin *= 0.7

            # M7 민감도 보정: 고민감 셀 margin 확대
            sens = sensitivity_map.get(seg_id, {})
            if sens and sens.get("sensitivity", 0) > 0.1:
                margin *= 1.5

            floor_rate = FLOOR_RATE_MAP.get(price_seg, 87.495)
            ratio_low = max(win_median - margin, floor_rate)
            ratio_high = min(win_median + margin, 94.0)
            center = win_median

            # 밴드 뒤집힘 보정: center < floor_rate인 경우
            # (T2A 저경쟁 등 투찰비율이 하한율보다 낮은 세그먼트)
            if ratio_low > ratio_high:
                ratio_low = max(win_median - margin, 70.0)
                ratio_high = max(win_median + margin, ratio_low + 0.5)

            # M3 피크 회피
            avoided_peaks = []
            for pb in peak_bins:
                if abs(center - pb) < 0.03:
                    if center > floor_rate + 0.05:
                        center -= 0.05
                    else:
                        center += 0.05
                    avoided_peaks.append(pb)

            # M6 안정성
            stability_pct = self._calc_stability(
                price_seg, win_median,
                monthly_by_seg.get(price_seg, []),
            )

            # 커버리지
            api_n = api_cnt_map.get(seg_id, 0)
            if api_n >= 20:
                coverage = "high"
            elif api_n >= 5:
                coverage = "medium"
            elif api_n >= 1:
                coverage = "low"
            else:
                coverage = "none"

            # 신뢰도
            confidence = min(
                1.0,
                (ntce_cnt / 1000) * 0.5 + (api_n / 50) * 0.5,
            )

            # CVaR 기반 위험
            max_score = MAX_SCORE_MAP.get(price_seg, 80)
            cvar_10 = sens.get("mean_cvar10")
            risk_score = (
                round(1.0 - (cvar_10 / max_score), 3)
                if cvar_10 else None
            )

            data_source = (
                "api+market" if coverage != "none" else "market_only"
            )

            policy.append({
                "segment_id": seg_id,
                "price_seg": price_seg,
                "comp_seg": comp_seg,
                "ratio_low": round(ratio_low, 2),
                "ratio_high": round(ratio_high, 2),
                "center": round(center, 2),
                "risk_score": risk_score,
                "tie_prob": None,
                "sample_n": ntce_cnt,
                "stability_pct": round(stability_pct, 1),
                "coverage_level": coverage,
                "confidence": round(confidence, 2),
                "data_source": data_source,
                "api_sample_n": api_n,
                "peak_avoided": avoided_peaks,
                "competition_adjusted": (
                    comp_seg in ("C100_199", "C200+")
                    and convergence is not None
                ),
                "updated_at": datetime.now().strftime("%Y-%m-%d"),
            })

        # 규칙 추출
        for price_seg in ["T5", "T4", "T3", "T2A", "T1"]:
            seg_cells = [
                p for p in policy if p["price_seg"] == price_seg
            ]
            if not seg_cells:
                continue

            high_comp = [
                p for p in seg_cells
                if p["comp_seg"] in ("C100_199", "C200+")
            ]
            low_comp = [
                p for p in seg_cells
                if p["comp_seg"] in ("C01_09", "C10_29")
            ]

            if high_comp and low_comp:
                hc_center = statistics.mean(
                    p["center"] for p in high_comp
                )
                lc_center = statistics.mean(
                    p["center"] for p in low_comp
                )
                if abs(hc_center - lc_center) > 0.3:
                    rule_id += 1
                    rules.append({
                        "id": rule_id,
                        "description": (
                            f"{price_seg} 고경쟁(100+) center "
                            f"{hc_center:.1f}% vs "
                            f"저경쟁(<30) {lc_center:.1f}% "
                            f"(차이 {hc_center - lc_center:+.1f}%p)"
                        ),
                        "segments": [
                            p["segment_id"]
                            for p in high_comp + low_comp
                        ],
                    })

            # 좁은 밴드 감지
            for p in seg_cells:
                band = p["ratio_high"] - p["ratio_low"]
                if 0 < band < 0.5:
                    rule_id += 1
                    rules.append({
                        "id": rule_id,
                        "description": (
                            f"{p['segment_id']}: 좁은 밴드 "
                            f"{band:.2f}%p → 정밀 투찰 필요"
                        ),
                        "segments": [p["segment_id"]],
                    })

        # 집계
        policy_ready = sum(
            1 for p in policy
            if p["coverage_level"] != "none" or p["sample_n"] >= 300
        )
        total_ntce = sum(p["sample_n"] for p in policy)
        ready_ntce = sum(
            p["sample_n"] for p in policy
            if p["coverage_level"] != "none" or p["sample_n"] >= 300
        )
        coverage_pct = (
            round(ready_ntce / total_ntce * 100, 1) if total_ntce else 0
        )
        avg_band = (
            round(
                statistics.mean(
                    p["ratio_high"] - p["ratio_low"] for p in policy
                ), 2,
            )
            if policy else 0
        )

        result = {
            "meta": {
                "module": "M8",
                "description": "세그먼트 정책 추출",
                "version": "v1",
            },
            "policy": policy,
            "summary": {
                "total_segments": len(policy),
                "policy_ready": policy_ready,
                "fallback_only": len(policy) - policy_ready,
                "avg_band_width": avg_band,
                "coverage_pct": coverage_pct,
                "rules_extracted": len(rules),
            },
            "rules": rules,
        }

        # segment_policy_v1.json 별도 저장
        policy_path = (
            BASE_DIR / "data" / "collected" / "segment_policy_v1.json"
        )
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(
            json.dumps(
                _clean(policy), ensure_ascii=False, indent=2, default=str
            ),
            encoding="utf-8",
        )
        self.stdout.write(
            self.style.SUCCESS(f"  정책 저장: {policy_path}")
        )

        self._print_m8(result)
        return result

    @staticmethod
    def _calc_stability(
        price_seg: str, win_median: float, monthly_rows: list,
    ) -> float:
        """월별 1순위 평균이 win_median 방향과 일치하는 비율(%)."""
        if not monthly_rows or len(monthly_rows) < 3:
            return 0.0
        recent = sorted(
            monthly_rows, key=lambda x: x["openg_month"]
        )[-6:]
        match_cnt = 0
        for row in recent:
            val = row.get("win_avg")
            if val is not None and abs(float(val) - win_median) < 1.5:
                match_cnt += 1
        return match_cnt / len(recent) * 100

    def _print_m8(self, data: dict):
        s = data["summary"]
        self.stdout.write(f"\n  총 세그먼트: {s['total_segments']}")
        self.stdout.write(f"  정책 적용 가능: {s['policy_ready']}")
        self.stdout.write(f"  Fallback only: {s['fallback_only']}")
        self.stdout.write(f"  평균 밴드: {s['avg_band_width']:.2f}%p")
        self.stdout.write(f"  커버리지: {s['coverage_pct']:.1f}%")
        self.stdout.write(f"  규칙: {s['rules_extracted']}개")

        if data["policy"]:
            self.stdout.write(
                f"\n  {'세그먼트':<14s} {'low':>6s} {'center':>7s} "
                f"{'high':>6s} {'커버':>5s} {'신뢰':>5s} {'안정':>5s}"
            )
            for p in data["policy"]:
                self.stdout.write(
                    f"  {p['segment_id']:<14s} "
                    f"{p['ratio_low']:>6.2f} {p['center']:>7.2f} "
                    f"{p['ratio_high']:>6.2f} "
                    f"{p['coverage_level']:>5s} "
                    f"{p['confidence']:>5.2f} "
                    f"{p['stability_pct']:>5.1f}"
                )

        if data["rules"]:
            self.stdout.write("\n  규칙:")
            for r in data["rules"][:10]:
                self.stdout.write(f"    [{r['id']}] {r['description']}")

    # ──────────────────────────────────────────────
    # 차트 생성 (6개)
    # ──────────────────────────────────────────────

    def _save_charts(self, results: dict):
        """6개 차트 생성."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
        except ImportError:
            self.stderr.write("  matplotlib 미설치 — 차트 생략")
            return

        chart_dir = BASE_DIR / "data" / "collected" / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)

        plt.rcParams["axes.unicode_minus"] = False
        for font_name in ["AppleGothic", "Malgun Gothic", "NanumGothic"]:
            if any(font_name in f.name for f in fm.fontManager.ttflist):
                plt.rcParams["font.family"] = font_name
                break

        chart_funcs = [
            ("M2", self._chart_m2, "cross_winrate_heatmap.png"),
            ("M3", self._chart_m3, "cross_ratio_peaks.png"),
            ("M4", self._chart_m4, "cross_competition_pressure.png"),
            ("M5", self._chart_m5, "cross_bidder_archetypes.png"),
            ("M6", self._chart_m6, "cross_regime_shift.png"),
            ("M7", self._chart_m7, "cross_scenario_sensitivity.png"),
        ]

        for module, func, filename in chart_funcs:
            mod_result = results.get(module)
            if mod_result and "error" not in mod_result:
                try:
                    fig = func(mod_result)
                    if fig:
                        fig.savefig(
                            chart_dir / filename,
                            dpi=150, bbox_inches="tight",
                        )
                        plt.close(fig)
                        self.stdout.write(f"  차트: {filename}")
                except Exception as e:
                    self.stderr.write(f"  차트 실패 ({filename}): {e}")

    def _chart_m2(self, data: dict):
        """승률면 히트맵 (가격대×경쟁강도)."""
        import matplotlib.pyplot as plt
        import numpy as np

        surface = data.get("surface", [])
        if not surface:
            return None

        price_segs = ["T5", "T4", "T3", "T2A", "T1"]
        comp_segs = [
            "C01_09", "C10_29", "C30_49",
            "C50_99", "C100_199", "C200+",
        ]

        grid = {}
        for row in surface:
            grid[(row["price_seg"], row["comp_seg"])] = float(
                row["win_median"] or 0
            )

        matrix = np.array([
            [grid.get((ps, cs), 0) for cs in comp_segs]
            for ps in price_segs
        ])

        fig, ax = plt.subplots(figsize=(10, 6))
        nonzero = matrix[matrix > 0]
        vmin = max(nonzero.min() - 0.5, 85) if nonzero.size else 85
        vmax = min(matrix.max() + 0.5, 93) if matrix.max() > 0 else 93

        im = ax.imshow(
            matrix, cmap="RdYlGn", aspect="auto",
            vmin=vmin, vmax=vmax,
        )
        ax.set_xticks(range(len(comp_segs)))
        ax.set_xticklabels(comp_segs, rotation=45, ha="right")
        ax.set_yticks(range(len(price_segs)))
        ax.set_yticklabels(price_segs)

        for i in range(len(price_segs)):
            for j in range(len(comp_segs)):
                val = matrix[i, j]
                if val > 0:
                    ax.text(
                        j, i, f"{val:.1f}",
                        ha="center", va="center",
                        fontsize=9, fontweight="bold",
                    )

        fig.colorbar(im, label="1순위 투찰비율 중앙값 (%)")
        ax.set_title("M2: 조건부 승률면 (가격대 x 경쟁강도)")
        ax.set_xlabel("경쟁강도")
        ax.set_ylabel("가격대")
        fig.tight_layout()
        return fig

    def _chart_m3(self, data: dict):
        """비율 밀도 + 과밀 지점."""
        import matplotlib.pyplot as plt

        bins = data.get("bins", [])
        if not bins:
            return None

        bin_totals: dict[float, int] = {}
        for b in bins:
            bv = float(b["bin"])
            bin_totals[bv] = bin_totals.get(bv, 0) + b["cnt"]

        xs = sorted(bin_totals.keys())
        ys = [bin_totals[x] for x in xs]

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.bar(range(len(xs)), ys, width=1.0, color="steelblue", alpha=0.7)

        peaks = data.get("peaks", [])
        for p in peaks:
            if p["bin"] in bin_totals:
                idx = xs.index(p["bin"])
                ax.annotate(
                    f"{p['bin']:.2f}%",
                    xy=(idx, bin_totals[p["bin"]]),
                    fontsize=7, color="red", fontweight="bold",
                    ha="center", va="bottom",
                )

        step = max(1, len(xs) // 20)
        ax.set_xticks(range(0, len(xs), step))
        ax.set_xticklabels(
            [f"{xs[i]:.1f}" for i in range(0, len(xs), step)],
            rotation=45, fontsize=7,
        )
        ax.set_title("M3: 투찰비율 밀도 + 과밀 지점 (86~94%)")
        ax.set_xlabel("투찰비율 (%)")
        ax.set_ylabel("건수")
        fig.tight_layout()
        return fig

    def _chart_m4(self, data: dict):
        """경쟁압력 1-2순위 gap."""
        import matplotlib.pyplot as plt

        deciles = data.get("deciles", [])
        if not deciles:
            return None

        xs = [d["bidder_decile"] for d in deciles]
        r1 = [float(d["r1_avg"] or 0) for d in deciles]
        r2 = [float(d["r2_avg"] or 0) for d in deciles]
        gaps = [float(d["gap_1_2"] or 0) for d in deciles]

        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(10, 8), sharex=True
        )

        ax1.plot(xs, r1, "o-", label="1순위", color="green")
        ax1.plot(xs, r2, "s-", label="2순위", color="orange")
        ax1.set_ylabel("투찰비율 (%)")
        ax1.set_title("M4: 경쟁압력 — 1·2순위 투찰비율")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.bar(xs, gaps, color="coral", alpha=0.7)
        ax2.axhline(
            y=0.05, color="red", linestyle="--", alpha=0.5,
            label="수렴 기준 (0.05)",
        )
        ax2.set_xlabel("경쟁 분위 (1=저 → 10=고)")
        ax2.set_ylabel("1-2순위 Gap (%p)")
        ax2.set_title("1-2순위 Gap")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        fig.tight_layout()
        return fig

    def _chart_m5(self, data: dict):
        """업체 아키타입 분포."""
        import matplotlib.pyplot as plt

        summary = data.get("summary", {})
        labels = ["ultra_fixed", "fixed", "adaptive", "dispersed"]
        sizes = [summary.get(l, {}).get("count", 0) for l in labels]
        colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336"]
        display_labels = ["초고정", "고정", "적응", "분산"]

        if sum(sizes) == 0:
            return None

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        ax1.pie(
            sizes, labels=display_labels, colors=colors,
            autopct="%1.1f%%", startangle=90,
            textprops={"fontsize": 10},
        )
        ax1.set_title("M5: 업체 아키타입 분포")

        by_seg = data.get("by_segment", [])
        if by_seg:
            segs = [r["price_seg"] for r in by_seg]
            bottom = [0.0] * len(segs)
            for i, atype in enumerate([
                "ultra_fixed_pct", "fixed_pct",
                "adaptive_pct", "dispersed_pct",
            ]):
                vals = [r.get(atype, 0) for r in by_seg]
                ax2.bar(
                    segs, vals, bottom=bottom,
                    color=colors[i], label=display_labels[i],
                )
                bottom = [b + v for b, v in zip(bottom, vals)]
            ax2.set_ylabel("비율 (%)")
            ax2.set_xlabel("가격대")
            ax2.set_title("가격대별 아키타입 구성")
            ax2.legend()

        fig.tight_layout()
        return fig

    def _chart_m6(self, data: dict):
        """시계열 변화점."""
        import matplotlib.pyplot as plt

        monthly = data.get("monthly", [])
        if not monthly:
            return None

        # T3 기준 (가장 볼륨 큰 세그먼트)
        t3 = [r for r in monthly if r["price_seg"] == "T3"]
        if not t3:
            t3 = monthly
        t3.sort(key=lambda x: x["openg_month"])

        months = [r["openg_month"] for r in t3]
        win_avgs = [
            float(r["win_avg"]) if r["win_avg"] else None for r in t3
        ]

        fig, ax = plt.subplots(figsize=(14, 5))
        valid = [
            (m, v) for m, v in zip(months, win_avgs) if v is not None
        ]
        if valid:
            ax.plot(
                [v[0] for v in valid], [v[1] for v in valid],
                "o-", color="steelblue",
            )

        for cp in data.get("changepoints", []):
            if cp["price_seg"] == "T3" and cp["month"] in months:
                ax.axvline(
                    x=cp["month"], color="red",
                    linestyle="--", alpha=0.5,
                )
                idx = months.index(cp["month"])
                if idx < len(win_avgs) and win_avgs[idx] is not None:
                    ax.annotate(
                        f"z={cp['z_score']:.1f}\n"
                        f"{cp['delta']:+.2f}",
                        xy=(cp["month"], win_avgs[idx]),
                        fontsize=8, color="red",
                    )

        step = max(1, len(months) // 15)
        ax.set_xticks(range(0, len(months), step))
        ax.set_xticklabels(
            [months[i] for i in range(0, len(months), step)],
            rotation=45, fontsize=8,
        )
        ax.set_title("M6: 1순위 투찰비율 시계열 (T3)")
        ax.set_xlabel("월")
        ax.set_ylabel("1순위 평균 투찰비율 (%)")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig

    def _chart_m7(self, data: dict):
        """시나리오 민감도 커브."""
        import matplotlib.pyplot as plt

        by_seg = data.get("by_segment", [])
        if not by_seg:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))

        labels = [
            f"{s['price_seg']}_{s['comp_seg']}" for s in by_seg
        ]
        expected = [s["mean_expected"] for s in by_seg]
        p10 = [s["mean_p10"] for s in by_seg]
        cvar = [s["mean_cvar10"] for s in by_seg]

        x = range(len(labels))
        width = 0.2
        ax.bar(
            [i - width for i in x], expected, width,
            label="기대점수", color="steelblue",
        )
        ax.bar(
            list(x), p10, width,
            label="P10", color="orange",
        )
        ax.bar(
            [i + width for i in x], cvar, width,
            label="CVaR10", color="red",
        )

        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
        ax.set_ylabel("가격점수")
        ax.set_title("M7: 세그먼트별 시나리오 민감도")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")
        fig.tight_layout()
        return fig

    # ──────────────────────────────────────────────
    # JSON 저장
    # ──────────────────────────────────────────────

    def _save_json(self, results: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "meta": {
                "command": "analyze_cross_table",
                "bc_id": "BC-37",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "description": (
                    "크로스테이블 종합 EDA + 세그먼트 정책 추출"
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
