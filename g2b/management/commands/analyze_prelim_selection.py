"""BC-43: 복수예비가격 선택 패턴 분석.

15개 복수예비가격 중 선택된 4개(is_drawn=True)의 위치별 빈도를 분석하여
시나리오 가중치 차등화의 근거를 확인한다.

Task 1: 데이터 품질 확인 (is_drawn 기반, 역산 불필요)
Task 2: 위치별 선택 빈도 + 카이제곱 검정

사용:
    python manage.py analyze_prelim_selection
    python manage.py analyze_prelim_selection --limit 100
    python manage.py analyze_prelim_selection --output data/collected/prelim_selection_analysis.json
"""

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from g2b.models import (
    BidApiCollectionLog,
    BidApiPrelimPrice,
    BidResult,
)
from g2b.services.bid_engine import WorkType, select_table

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Command(BaseCommand):
    help = "BC-43: 복수예비가격 선택 패턴 분석 (위치별 빈도 + 카이제곱)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=0,
            help="실행 건수 제한 (디버깅용, 0=전체)",
        )
        parser.add_argument(
            "--output", type=str,
            default="data/collected/prelim_selection_analysis.json",
            help="JSON 결과 저장 경로",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        output_path = options["output"]

        # ── Task 1: 데이터 품질 확인 ──
        self.stdout.write("\n=== Task 1: 데이터 품질 확인 ===\n")
        records = self._load_records(limit)
        quality = self._check_quality(records)
        self._print_quality(quality)

        valid_records = quality["valid_records"]
        if not valid_records:
            self.stdout.write(self.style.ERROR("유효 데이터 없음, 종료"))
            return

        # ── Task 2: 위치별 선택 빈도 분석 ──
        self.stdout.write("\n=== Task 2: 위치별 선택 빈도 분석 ===\n")
        freq_result = self._analyze_position_frequency(valid_records)
        self._print_frequency(freq_result)

        # 별표별 분석
        self.stdout.write("\n--- 별표별 분석 ---")
        by_table = self._analyze_by_table(valid_records)
        self._print_by_table(by_table)

        # 경쟁자수별 분석
        self.stdout.write("\n--- 경쟁자수별 분석 ---")
        by_competition = self._analyze_by_competition(valid_records)
        self._print_by_competition(by_competition)

        # ── JSON 저장 ──
        self._save_json(quality, freq_result, by_table, by_competition, output_path)

    # ──────────────────────────────────────────
    # Task 1: 데이터 로드 + 품질 확인
    # ──────────────────────────────────────────

    def _load_records(self, limit: int) -> list[dict]:
        """15개 비0 예비가격 보유 공고의 복수예비가격 + is_drawn 로드."""
        from django.db.models import Count, Q

        # 15개 비0 예비가격 + 4개 drawn 공고만 직접 필터
        valid_keys = list(
            BidApiPrelimPrice.objects
            .values("bid_ntce_no", "bid_ntce_ord")
            .annotate(
                nonzero=Count("id", filter=Q(basis_planned_price__gt=0)),
                drawn=Count("id", filter=Q(is_drawn=True)),
            )
            .filter(nonzero=15, drawn=4)
            .values_list("bid_ntce_no", "bid_ntce_ord")
        )
        self.stdout.write(f"  15개+drawn=4 공고: {len(valid_keys)}건")

        if limit > 0:
            valid_keys = valid_keys[:limit]

        records = []
        for ntce_no, ntce_ord in valid_keys:
            rows = list(
                BidApiPrelimPrice.objects
                .filter(
                    bid_ntce_no=ntce_no,
                    bid_ntce_ord=ntce_ord,
                    basis_planned_price__gt=0,
                )
                .order_by("sequence_no")
                .values(
                    "sequence_no", "basis_planned_price",
                    "is_drawn", "draw_count", "planned_price",
                )
            )
            if len(rows) != 15:
                continue

            records.append({
                "ntce_no": ntce_no,
                "ntce_ord": ntce_ord,
                "rows": rows,
                "planned_price": rows[0]["planned_price"],
            })

        self.stdout.write(f"  로드 완료: {len(records)}건")
        return records

    def _check_quality(self, records: list[dict]) -> dict:
        """데이터 품질 확인: 행 수, is_drawn 개수, 예정가격 일치."""
        total = len(records)
        has_15_rows = 0
        drawn_4 = 0
        drawn_dist = Counter()
        price_match = 0
        price_mismatch_examples = []
        valid_records = []

        for rec in records:
            rows = rec["rows"]
            n_rows = len(rows)
            nonzero_rows = [r for r in rows if r["basis_planned_price"] > 0]
            n_nonzero = len(nonzero_rows)
            drawn_rows = [r for r in rows if r["is_drawn"]]
            n_drawn = len(drawn_rows)
            drawn_dist[n_drawn] += 1

            if n_nonzero == 15:
                has_15_rows += 1

            if n_drawn == 4 and n_nonzero == 15:
                drawn_4 += 1

                # 예정가격 일치 확인
                drawn_prices = [r["basis_planned_price"] for r in drawn_rows]
                avg4 = sum(drawn_prices) / 4
                est = math.floor(avg4) if avg4 != int(avg4) else int(avg4)
                if est == rec["planned_price"]:
                    price_match += 1
                else:
                    if len(price_mismatch_examples) < 5:
                        price_mismatch_examples.append({
                            "ntce_no": rec["ntce_no"],
                            "computed": est,
                            "actual": rec["planned_price"],
                            "diff": abs(est - rec["planned_price"]),
                        })

                valid_records.append({
                    **rec,
                    "prices_15": [r["basis_planned_price"] for r in nonzero_rows],
                    "drawn_prices": drawn_prices,
                    "draw_counts": [r["draw_count"] for r in nonzero_rows],
                })

        return {
            "total": total,
            "has_15_rows": has_15_rows,
            "drawn_4": drawn_4,
            "drawn_dist": dict(sorted(drawn_dist.items())),
            "price_match": price_match,
            "price_mismatch_examples": price_mismatch_examples,
            "valid_records": valid_records,
        }

    def _print_quality(self, q: dict):
        self.stdout.write(f"  전체 공고: {q['total']}건")
        self.stdout.write(f"  15개 예비가격 보유: {q['has_15_rows']}건")
        self.stdout.write(f"  is_drawn=True 4개: {q['drawn_4']}건")
        self.stdout.write(f"  예정가격 일치: {q['price_match']}/{q['drawn_4']}건")
        self.stdout.write(f"  유효 레코드: {len(q['valid_records'])}건")
        self.stdout.write(f"\n  is_drawn 개수 분포:")
        for k, v in q["drawn_dist"].items():
            self.stdout.write(f"    {k}개: {v}건")
        if q["price_mismatch_examples"]:
            self.stdout.write(f"\n  예정가격 불일치 예시:")
            for ex in q["price_mismatch_examples"]:
                self.stdout.write(
                    f"    {ex['ntce_no']}: 계산={ex['computed']:,} "
                    f"실제={ex['actual']:,} (차이={ex['diff']}원)"
                )

    # ──────────────────────────────────────────
    # Task 2: 위치별 선택 빈도 분석
    # ──────────────────────────────────────────

    def _analyze_position_frequency(self, records: list[dict]) -> dict:
        """15개 예비가격을 금액순 정렬 후 위치별 선택 빈도 계산.

        주의: 동일 금액 예비가격이 존재할 수 있으므로 enumerate 기반
        used 플래그 방식으로 위치 매핑 (BC-43 주의사항 #2).
        """
        position_counts = [0.0] * 15
        total_selections = 0.0

        for rec in records:
            sorted_prices = sorted(rec["prices_15"])
            drawn_prices = rec["drawn_prices"]

            # enumerate 기반 위치 매핑 (동일 금액 안전)
            used = [False] * 15
            for price in drawn_prices:
                for i, (sp, u) in enumerate(zip(sorted_prices, used)):
                    if sp == price and not u:
                        position_counts[i] += 1.0
                        used[i] = True
                        break
            total_selections += 4.0

        # 확률 계산
        position_probs = [c / total_selections for c in position_counts]
        uniform_prob = 4.0 / 15.0  # 26.67%

        # 카이제곱 검정
        expected_count = total_selections * uniform_prob / 4.0  # 위치당 기대 선택수
        # 실제: N건 × (4/15) = 위치당 기대 선택수
        expected_per_pos = total_selections / 15.0
        chi2 = sum(
            (obs - expected_per_pos) ** 2 / expected_per_pos
            for obs in position_counts
        )
        df = 14  # 15 - 1
        p_value = self._chi2_p_value(chi2, df)

        # 편차 분석
        deviations = [p - uniform_prob for p in position_probs]
        max_dev = max(abs(d) for d in deviations)
        max_dev_pos = deviations.index(max(deviations, key=abs))

        return {
            "n_records": len(records),
            "total_selections": total_selections,
            "position_counts": position_counts,
            "position_probs": position_probs,
            "uniform_prob": uniform_prob,
            "deviations": deviations,
            "max_deviation": max_dev,
            "max_deviation_pos": max_dev_pos + 1,  # 1-indexed
            "chi2": chi2,
            "df": df,
            "p_value": p_value,
        }

    def _chi2_p_value(self, chi2: float, df: int) -> float:
        """카이제곱 p-value 근사 (scipy 없이).

        Wilson-Hilferty 근사법으로 정규분포 변환 후 p-value 계산.
        """
        if chi2 <= 0:
            return 1.0
        # Wilson-Hilferty transformation
        z = ((chi2 / df) ** (1.0 / 3.0) - (1 - 2.0 / (9 * df))) / math.sqrt(
            2.0 / (9 * df)
        )
        # Standard normal CDF approximation (Abramowitz & Stegun)
        if z < -8:
            return 1.0
        if z > 8:
            return 0.0
        p = 0.5 * math.erfc(z / math.sqrt(2))
        return p

    def _print_frequency(self, r: dict):
        self.stdout.write(f"  분석 대상: {r['n_records']}건")
        self.stdout.write(f"  균등 확률: {r['uniform_prob']:.4f} (4/15 = 26.67%)")
        self.stdout.write(f"\n  {'위치':>4} {'선택수':>8} {'확률':>8} {'편차':>8} {'막대'}")
        self.stdout.write(f"  {'─' * 4} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 20}")

        for i in range(15):
            cnt = r["position_counts"][i]
            prob = r["position_probs"][i]
            dev = r["deviations"][i]
            bar_len = int(prob * 150)
            bar = "█" * bar_len
            dev_str = f"{dev:+.2%}"
            self.stdout.write(
                f"  {i + 1:4d} {cnt:8.0f} {prob:8.4f} {dev_str:>8} {bar}"
            )

        self.stdout.write(f"\n  카이제곱 통계량: {r['chi2']:.2f} (df={r['df']})")
        self.stdout.write(f"  p-value: {r['p_value']:.6f}")
        if r["p_value"] < 0.05:
            self.stdout.write(
                self.style.SUCCESS(f"  → 유의미한 비균등성 (p < 0.05)")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"  → 균등에 가까움 (p >= 0.05)")
            )
        self.stdout.write(
            f"  최대 편차: 위치 {r['max_deviation_pos']} "
            f"({r['max_deviation']:+.2%})"
        )

    # ──────────────────────────────────────────
    # 세그먼트별 분석
    # ──────────────────────────────────────────

    def _get_presume_and_bidder(self, records: list[dict]) -> dict:
        """BidResult에서 추정가격 + 경쟁자수 조회."""
        from django.db import connection

        keys = [(r["ntce_no"], r["ntce_ord"]) for r in records]
        if not keys:
            return {}

        placeholders = ", ".join(["(%s, %s)"] * len(keys))
        flat_params = []
        for n, o in keys:
            flat_params.extend([n, o])

        sql = f"""
            SELECT DISTINCT ON (bid_ntce_no, bid_ntce_ord)
                bid_ntce_no, bid_ntce_ord, presume_price, bidder_cnt
            FROM g2b_bidresult
            WHERE (bid_ntce_no, bid_ntce_ord) IN ({placeholders})
              AND presume_price > 0
              AND openg_rank = '1'
            ORDER BY bid_ntce_no, bid_ntce_ord, bid_amt ASC
        """

        result = {}
        with connection.cursor() as cursor:
            cursor.execute(sql, flat_params)
            for row in cursor.fetchall():
                result[(row[0], row[1])] = {
                    "presume_price": row[2],
                    "bidder_cnt": row[3],
                }
        return result

    def _analyze_by_table(self, records: list[dict]) -> dict:
        """별표별 위치 빈도 분석."""
        meta = self._get_presume_and_bidder(records)

        by_table = defaultdict(list)
        for rec in records:
            key = (rec["ntce_no"], rec["ntce_ord"])
            info = meta.get(key)
            if not info:
                continue
            table = select_table(info["presume_price"], WorkType.CONSTRUCTION)
            by_table[table.value].append(rec)

        result = {}
        for table_name, recs in sorted(by_table.items()):
            if len(recs) < 10:
                continue
            freq = self._analyze_position_frequency(recs)
            result[table_name] = {
                "count": len(recs),
                "chi2": freq["chi2"],
                "p_value": freq["p_value"],
                "max_deviation": freq["max_deviation"],
                "max_deviation_pos": freq["max_deviation_pos"],
                "position_probs": freq["position_probs"],
            }
        return result

    def _print_by_table(self, by_table: dict):
        self.stdout.write(
            f"\n  {'별표':<12} {'건수':>6} {'χ²':>8} {'p-value':>10} "
            f"{'최대편차':>8} {'위치':>4}"
        )
        self.stdout.write(f"  {'─' * 12} {'─' * 6} {'─' * 8} {'─' * 10} {'─' * 8} {'─' * 4}")
        for name, d in sorted(by_table.items()):
            sig = "***" if d["p_value"] < 0.001 else "**" if d["p_value"] < 0.01 else "*" if d["p_value"] < 0.05 else ""
            self.stdout.write(
                f"  {name:<12} {d['count']:>6} {d['chi2']:>8.2f} "
                f"{d['p_value']:>10.6f} {d['max_deviation']:>+8.2%} "
                f"{d['max_deviation_pos']:>4} {sig}"
            )

    def _analyze_by_competition(self, records: list[dict]) -> dict:
        """경쟁자수별 위치 빈도 분석."""
        meta = self._get_presume_and_bidder(records)

        buckets = {
            "~30명": lambda cnt: cnt and cnt < 30,
            "30~99명": lambda cnt: cnt and 30 <= cnt < 100,
            "100~199명": lambda cnt: cnt and 100 <= cnt < 200,
            "200+명": lambda cnt: cnt and cnt >= 200,
        }

        by_bucket = defaultdict(list)
        for rec in records:
            key = (rec["ntce_no"], rec["ntce_ord"])
            info = meta.get(key)
            if not info:
                continue
            cnt = info["bidder_cnt"]
            for bname, bfn in buckets.items():
                if bfn(cnt):
                    by_bucket[bname].append(rec)
                    break

        result = {}
        for bname, recs in by_bucket.items():
            if len(recs) < 10:
                result[bname] = {"count": len(recs), "skip": True}
                continue
            freq = self._analyze_position_frequency(recs)
            result[bname] = {
                "count": len(recs),
                "skip": False,
                "chi2": freq["chi2"],
                "p_value": freq["p_value"],
                "max_deviation": freq["max_deviation"],
                "max_deviation_pos": freq["max_deviation_pos"],
                "position_probs": freq["position_probs"],
            }
        return result

    def _print_by_competition(self, by_comp: dict):
        self.stdout.write(
            f"\n  {'경쟁자수':<12} {'건수':>6} {'χ²':>8} {'p-value':>10} "
            f"{'최대편차':>8} {'위치':>4}"
        )
        self.stdout.write(f"  {'─' * 12} {'─' * 6} {'─' * 8} {'─' * 10} {'─' * 8} {'─' * 4}")
        for name in ["~30명", "30~99명", "100~199명", "200+명"]:
            d = by_comp.get(name)
            if not d:
                continue
            if d.get("skip"):
                self.stdout.write(f"  {name:<12} {d['count']:>6}  (건수 부족, 생략)")
                continue
            sig = "***" if d["p_value"] < 0.001 else "**" if d["p_value"] < 0.01 else "*" if d["p_value"] < 0.05 else ""
            self.stdout.write(
                f"  {name:<12} {d['count']:>6} {d['chi2']:>8.2f} "
                f"{d['p_value']:>10.6f} {d['max_deviation']:>+8.2%} "
                f"{d['max_deviation_pos']:>4} {sig}"
            )

    # ──────────────────────────────────────────
    # JSON 저장
    # ──────────────────────────────────────────

    def _save_json(self, quality, freq_result, by_table, by_competition, path):
        output = {
            "meta": {
                "command": "analyze_prelim_selection",
                "bc_issue": "BC-43",
                "created_at": datetime.now().isoformat(),
                "description": "복수예비가격 선택 패턴 분석 (is_drawn 기반)",
            },
            "quality": {
                "total": quality["total"],
                "has_15_rows": quality["has_15_rows"],
                "drawn_4": quality["drawn_4"],
                "price_match": quality["price_match"],
                "valid_count": len(quality["valid_records"]),
                "drawn_distribution": quality["drawn_dist"],
            },
            "overall_frequency": {
                "n_records": freq_result["n_records"],
                "position_probs": freq_result["position_probs"],
                "deviations": freq_result["deviations"],
                "chi2": freq_result["chi2"],
                "df": freq_result["df"],
                "p_value": freq_result["p_value"],
                "max_deviation": freq_result["max_deviation"],
                "max_deviation_pos": freq_result["max_deviation_pos"],
            },
            "by_table": {
                k: {kk: vv for kk, vv in v.items()}
                for k, v in by_table.items()
            },
            "by_competition": {
                k: {kk: vv for kk, vv in v.items()}
                for k, v in by_competition.items()
            },
        }

        out_path = BASE_DIR / path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f"\n  JSON 저장: {out_path}"))
