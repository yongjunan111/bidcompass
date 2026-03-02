"""BC-33: 최적투찰 백테스트.

558건 나의방 데이터로 최적투찰 엔진을 실행하여:
  - 최적 bid vs 파일럿(나의) bid 가격점수 비교
  - 최적 bid vs 1순위 bid 가격점수 비교
  - 기대점수 vs 실제점수 예측력 검증

사용:
    python manage.py simulate_optimal_bid
    python manage.py simulate_optimal_bid --limit 5 --verbosity 2
    python manage.py simulate_optimal_bid --output data/collected/optimal_bid_result.json
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand

from g2b.services.bid_engine import (
    AValueItems,
    TableType,
    WorkType,
    calculate_a_value,
    select_table,
    TABLE_PARAMS_MAP,
    UNIT_EOUK,
)
from g2b.services.optimal_bid import (
    OptimalBidInput,
    evaluate_bid,
    find_optimal_bid,
)
from g2b.management.commands.simulate_historical import (
    load_excel_data,
    load_a_values,
    load_preliminary_prices,
    parse_amount,
    A_VALUE_FIELD_MAP,
    EXCEL_FILES,
    A_VALUES_JSON,
    PRELIM_PRICES_JSON,
    CONSTRUCTION_KEYWORDS,
    BASE_DIR,
)


class Command(BaseCommand):
    help = "BC-33: 최적투찰 백테스트 (558건 나의방 데이터)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=0,
            help="실행 건수 제한 (디버깅용, 0=전체)",
        )
        parser.add_argument(
            "--output", type=str, default="",
            help="JSON 결과 저장 경로",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        output_path = options["output"]
        verbosity = options["verbosity"]

        # 1. 데이터 로드
        self.stdout.write("엑셀 파일 로드 중...")
        rows = load_excel_data(EXCEL_FILES)
        self.stdout.write(f"  {len(rows)}건 로드 완료")

        if limit > 0:
            rows = rows[:limit]
            self.stdout.write(f"  --limit {limit} 적용")

        self.stdout.write("A값 JSON 로드 중...")
        a_values = load_a_values(A_VALUES_JSON)
        self.stdout.write(f"  {len(a_values)}건 로드 완료")

        self.stdout.write("복수예비가격 JSON 로드 중...")
        prelim_prices_data = load_preliminary_prices(PRELIM_PRICES_JSON)
        self.stdout.write(f"  {len(prelim_prices_data)}건 로드 완료")

        # 2. 백테스트 실행
        results = self._run_backtest(
            rows, a_values, prelim_prices_data, verbosity,
        )

        # 3. 리포트 출력
        self._print_summary(results)
        self._print_vs_pilot(results)
        self._print_vs_rank1(results)
        self._print_prediction_accuracy(results)
        self._print_by_table(results)

        # 4. JSON 저장
        if output_path:
            self._save_json(results, output_path)

    def _run_backtest(
        self,
        rows: list[dict],
        a_values: dict[str, AValueItems],
        prelim_prices_data: dict[str, list],
        verbosity: int,
    ) -> dict:
        records = []
        stats = {
            "total": len(rows),
            "eligible": 0,
            "processed": 0,
            "skip_no_det_price": 0,
            "skip_no_a_value": 0,
            "skip_no_prelim": 0,
            "skip_prelim_under_4": 0,
            "skip_out_of_scope": 0,
            "error": 0,
        }

        table_results = defaultdict(lambda: {
            "count": 0,
            "our_scores": [],
            "pilot_scores": [],
            "rank1_scores": [],
            "improvements": [],
        })

        for i, row in enumerate(rows):
            bid_no = row["bid_no"]
            det_price = row["det_price"]
            est_price = row["est_price"]

            # det_price 필수 (검증용)
            if det_price is None or det_price <= 0:
                stats["skip_no_det_price"] += 1
                continue

            # 추정가격 (라우팅용)
            routing_price = (
                est_price if (est_price and est_price > 0) else det_price
            )

            # WorkType (558건 전부 건설)
            work_type = WorkType.CONSTRUCTION

            # 테이블 라우팅
            try:
                table_type = select_table(routing_price, work_type)
            except ValueError:
                stats["error"] += 1
                continue

            if table_type == TableType.OUT_OF_SCOPE:
                stats["skip_out_of_scope"] += 1
                continue

            # A값 로드
            a_value_items = a_values.get(bid_no)
            if a_value_items is None:
                stats["skip_no_a_value"] += 1
                continue

            try:
                a_value = calculate_a_value(a_value_items)
            except ValueError:
                stats["error"] += 1
                continue

            # 복수예비가격 로드
            prelim_items = prelim_prices_data.get(bid_no)
            if not prelim_items:
                stats["skip_no_prelim"] += 1
                continue

            # bsisPlnprc 추출
            bsis_prices = []
            for item in prelim_items:
                val = item.get("bsisPlnprc", "")
                if val and str(val).strip():
                    bsis_prices.append(int(val))

            if len(bsis_prices) < 4:
                stats["skip_prelim_under_4"] += 1
                continue

            stats["eligible"] += 1

            # OptimalBidInput 구성 (정답 데이터 오염 없음 — det_price 미전달)
            inp = OptimalBidInput(
                preliminary_prices=bsis_prices,
                a_value=a_value,
                table_type=table_type,
                presume_price=routing_price,
            )

            try:
                opt_result = find_optimal_bid(inp)
            except Exception as e:
                stats["error"] += 1
                if verbosity >= 2:
                    self.stderr.write(f"  오류 {bid_no}: {e}")
                continue

            stats["processed"] += 1

            # evaluate: 우리 bid
            our_eval = evaluate_bid(
                opt_result.recommended_bid, det_price, a_value, table_type,
            )

            rec = {
                "bid_no": bid_no,
                "table_type": table_type.value,
                "det_price": det_price,
                "a_value": a_value,
                "n_prelim": len(bsis_prices),
                "n_scenarios": opt_result.n_scenarios,
                "our_bid": opt_result.recommended_bid,
                "our_expected_score": round(opt_result.expected_score, 2),
                "our_actual_score": round(our_eval.score, 2),
                "our_ratio": round(our_eval.ratio, 4),
                "min_scenario_score": round(opt_result.min_scenario_score, 2),
                "max_scenario_score": round(opt_result.max_scenario_score, 2),
                "scan_steps": opt_result.scan_steps,
            }

            # evaluate: 파일럿(나의) bid
            my_bid = row["my_bid"]
            if my_bid is not None and my_bid > 0 and a_value < det_price:
                pilot_eval = evaluate_bid(my_bid, det_price, a_value, table_type)
                rec["pilot_bid"] = my_bid
                rec["pilot_score"] = round(pilot_eval.score, 2)
                rec["improvement"] = round(our_eval.score - pilot_eval.score, 2)

                table_results[table_type.value]["pilot_scores"].append(
                    pilot_eval.score
                )
                table_results[table_type.value]["improvements"].append(
                    our_eval.score - pilot_eval.score
                )

            # evaluate: 1순위 bid
            rank1_bid = row["rank1_bid"]
            if rank1_bid is not None and rank1_bid > 0 and a_value < det_price:
                rank1_eval = evaluate_bid(
                    rank1_bid, det_price, a_value, table_type,
                )
                rec["rank1_bid"] = rank1_bid
                rec["rank1_score"] = round(rank1_eval.score, 2)
                rec["gap_vs_rank1"] = round(our_eval.score - rank1_eval.score, 2)

                table_results[table_type.value]["rank1_scores"].append(
                    rank1_eval.score
                )

            table_results[table_type.value]["count"] += 1
            table_results[table_type.value]["our_scores"].append(our_eval.score)

            records.append(rec)

            if verbosity >= 2:
                imp = rec.get("improvement", "-")
                self.stdout.write(
                    f"  [{i+1}] {bid_no} "
                    f"our={rec['our_actual_score']:.1f} "
                    f"pilot={rec.get('pilot_score', '-')} "
                    f"imp={imp}"
                )

        return {
            "stats": stats,
            "records": records,
            "table_results": dict(table_results),
        }

    # ──────────────────────────────────────────
    # 리포트 출력
    # ──────────────────────────────────────────

    def _print_summary(self, results: dict):
        s = results["stats"]
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("  최적투찰 백테스트 (BC-33)")
        self.stdout.write("=" * 60)
        self.stdout.write(f"전체 공고:              {s['total']}건")
        self.stdout.write(f"적격 레코드:            {s['eligible']}건")
        self.stdout.write(f"  처리 성공:            {s['processed']}건")
        self.stdout.write(f"스킵:")
        self.stdout.write(f"  예정가격 없음:        {s['skip_no_det_price']}건")
        self.stdout.write(f"  A값 없음:             {s['skip_no_a_value']}건")
        self.stdout.write(f"  복수예비가격 없음:    {s['skip_no_prelim']}건")
        self.stdout.write(f"  예비가격 < 4개:       {s['skip_prelim_under_4']}건")
        self.stdout.write(f"  OUT_OF_SCOPE:         {s['skip_out_of_scope']}건")
        self.stdout.write(f"에러:                   {s['error']}건")

    def _print_vs_pilot(self, results: dict):
        records = results["records"]
        has_pilot = [r for r in records if "pilot_score" in r]

        self.stdout.write("")
        self.stdout.write("[우리 vs 파일럿 (나의투찰)]")
        self.stdout.write(f"대상: {len(has_pilot)}건")

        if not has_pilot:
            return

        n = len(has_pilot)
        wins = sum(1 for r in has_pilot if r["improvement"] > 0)
        ties = sum(1 for r in has_pilot if r["improvement"] == 0)
        losses = n - wins - ties

        self.stdout.write(f"  승 (우리 > 파일럿): {wins:>4d}건 ({wins/n*100:.1f}%)")
        self.stdout.write(f"  무 (동일):          {ties:>4d}건 ({ties/n*100:.1f}%)")
        self.stdout.write(f"  패 (우리 < 파일럿): {losses:>4d}건 ({losses/n*100:.1f}%)")

        avg_imp = sum(r["improvement"] for r in has_pilot) / n
        self.stdout.write(f"  평균 개선도: {avg_imp:+.2f}점")

        # 개선도 분포
        big_win = sum(1 for r in has_pilot if r["improvement"] >= 5)
        small_win = sum(1 for r in has_pilot if 0 < r["improvement"] < 5)
        small_loss = sum(1 for r in has_pilot if -5 < r["improvement"] < 0)
        big_loss = sum(1 for r in has_pilot if r["improvement"] <= -5)
        self.stdout.write(f"\n  개선도 분포:")
        self.stdout.write(f"    +5점 이상:  {big_win:>4d}건")
        self.stdout.write(f"    +0~5점:     {small_win:>4d}건")
        self.stdout.write(f"    -5~0점:     {small_loss:>4d}건")
        self.stdout.write(f"    -5점 이하:  {big_loss:>4d}건")

    def _print_vs_rank1(self, results: dict):
        records = results["records"]
        has_rank1 = [r for r in records if "rank1_score" in r]

        self.stdout.write("")
        self.stdout.write("[우리 vs 1순위]")
        self.stdout.write(f"대상: {len(has_rank1)}건")

        if not has_rank1:
            return

        n = len(has_rank1)
        wins = sum(1 for r in has_rank1 if r["gap_vs_rank1"] > 0)
        ties = sum(1 for r in has_rank1 if r["gap_vs_rank1"] == 0)
        losses = n - wins - ties

        self.stdout.write(f"  승 (우리 > 1순위):  {wins:>4d}건 ({wins/n*100:.1f}%)")
        self.stdout.write(f"  무 (동일):          {ties:>4d}건 ({ties/n*100:.1f}%)")
        self.stdout.write(f"  패 (우리 < 1순위):  {losses:>4d}건 ({losses/n*100:.1f}%)")

        avg_gap = sum(r["gap_vs_rank1"] for r in has_rank1) / n
        self.stdout.write(f"  평균 격차: {avg_gap:+.2f}점")

    def _print_prediction_accuracy(self, results: dict):
        records = results["records"]
        has_both = [
            r for r in records
            if "our_expected_score" in r and "our_actual_score" in r
        ]

        self.stdout.write("")
        self.stdout.write("[기대점수 vs 실제점수 (예측력 검증)]")

        if not has_both:
            self.stdout.write("  (데이터 없음)")
            return

        diffs = [
            abs(r["our_expected_score"] - r["our_actual_score"])
            for r in has_both
        ]
        avg_diff = sum(diffs) / len(diffs)
        max_diff = max(diffs)

        self.stdout.write(f"  대상: {len(has_both)}건")
        self.stdout.write(f"  평균 |기대-실제|: {avg_diff:.2f}점")
        self.stdout.write(f"  최대 |기대-실제|: {max_diff:.2f}점")

        # 정확도 구간
        within_1 = sum(1 for d in diffs if d <= 1)
        within_5 = sum(1 for d in diffs if d <= 5)
        within_10 = sum(1 for d in diffs if d <= 10)
        n = len(diffs)
        self.stdout.write(f"  1점 이내: {within_1}/{n} ({within_1/n*100:.1f}%)")
        self.stdout.write(f"  5점 이내: {within_5}/{n} ({within_5/n*100:.1f}%)")
        self.stdout.write(f"  10점 이내: {within_10}/{n} ({within_10/n*100:.1f}%)")

    def _print_by_table(self, results: dict):
        table_results = results["table_results"]

        self.stdout.write("")
        self.stdout.write("[별표별 분석]")
        self.stdout.write(
            f"{'별표':<12s} {'건수':>4s} {'우리평균':>8s} "
            f"{'파일럿평균':>10s} {'개선도':>8s} {'1순위평균':>10s}"
        )

        for table in sorted(table_results.keys()):
            tr = table_results[table]
            n = tr["count"]
            our_avg = sum(tr["our_scores"]) / n if n else 0

            pilot_avg = "-"
            if tr["pilot_scores"]:
                pilot_avg = f"{sum(tr['pilot_scores'])/len(tr['pilot_scores']):.1f}"

            imp_avg = "-"
            if tr["improvements"]:
                imp_avg = f"{sum(tr['improvements'])/len(tr['improvements']):+.1f}"

            rank1_avg = "-"
            if tr["rank1_scores"]:
                rank1_avg = f"{sum(tr['rank1_scores'])/len(tr['rank1_scores']):.1f}"

            self.stdout.write(
                f"{table:<12s} {n:>4d} {our_avg:>8.1f} "
                f"{pilot_avg:>10s} {imp_avg:>8s} {rank1_avg:>10s}"
            )

    # ──────────────────────────────────────────
    # JSON 저장
    # ──────────────────────────────────────────

    def _save_json(self, results: dict, output_path: str):
        path = Path(output_path)
        if not path.is_absolute():
            path = BASE_DIR / path

        path.parent.mkdir(parents=True, exist_ok=True)

        # 별표별 요약 계산
        by_table = {}
        for table, tr in results["table_results"].items():
            n = tr["count"]
            entry = {"count": n}

            if tr["our_scores"]:
                entry["our_avg_score"] = round(
                    sum(tr["our_scores"]) / len(tr["our_scores"]), 2
                )
            if tr["pilot_scores"]:
                entry["pilot_avg_score"] = round(
                    sum(tr["pilot_scores"]) / len(tr["pilot_scores"]), 2
                )
            if tr["improvements"]:
                entry["avg_improvement"] = round(
                    sum(tr["improvements"]) / len(tr["improvements"]), 2
                )
            if tr["rank1_scores"]:
                entry["rank1_avg_score"] = round(
                    sum(tr["rank1_scores"]) / len(tr["rank1_scores"]), 2
                )
            by_table[table] = entry

        # 비교 요약
        records = results["records"]
        has_pilot = [r for r in records if "pilot_score" in r]
        has_rank1 = [r for r in records if "rank1_score" in r]

        comparison_pilot = {}
        if has_pilot:
            n = len(has_pilot)
            comparison_pilot = {
                "total": n,
                "wins": sum(1 for r in has_pilot if r["improvement"] > 0),
                "ties": sum(1 for r in has_pilot if r["improvement"] == 0),
                "losses": sum(1 for r in has_pilot if r["improvement"] < 0),
                "avg_improvement": round(
                    sum(r["improvement"] for r in has_pilot) / n, 2
                ),
            }

        comparison_rank1 = {}
        if has_rank1:
            n = len(has_rank1)
            comparison_rank1 = {
                "total": n,
                "wins": sum(1 for r in has_rank1 if r["gap_vs_rank1"] > 0),
                "ties": sum(1 for r in has_rank1 if r["gap_vs_rank1"] == 0),
                "losses": sum(1 for r in has_rank1 if r["gap_vs_rank1"] < 0),
                "avg_gap": round(
                    sum(r["gap_vs_rank1"] for r in has_rank1) / n, 2
                ),
            }

        # 예측력
        has_pred = [
            r for r in records
            if "our_expected_score" in r and "our_actual_score" in r
        ]
        prediction = {}
        if has_pred:
            diffs = [
                abs(r["our_expected_score"] - r["our_actual_score"])
                for r in has_pred
            ]
            prediction = {
                "avg_expected_vs_actual_diff": round(sum(diffs) / len(diffs), 2),
                "max_diff": round(max(diffs), 2),
            }

        report = {
            "meta": {
                "command": "simulate_optimal_bid",
                "bc_id": "BC-33",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "description": "최적투찰 백테스트 결과",
            },
            "stats": results["stats"],
            "comparison_vs_pilot": comparison_pilot,
            "comparison_vs_rank1": comparison_rank1,
            "prediction_accuracy": prediction,
            "by_table": by_table,
            "records": records,
        }

        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"JSON 저장: {path}"))
