"""BC-46: 하한율 미달 방지 시뮬레이션.

부모님 회사 558건 데이터에서:
  - Level 1: 하한율 표시로 사용자가 회피 가능한 건수 (경고 방지)
  - Level 2: 엔진 추천 bid가 자동으로 하한율 위인 건수 (엔진 자동 방지)

사용:
    python manage.py simulate_floor_prevention
    python manage.py simulate_floor_prevention --verbosity 2
"""

import math
from collections import defaultdict

from django.core.management.base import BaseCommand

from g2b.services.bid_engine import (
    AValueItems,
    TableType,
    WorkType,
    calculate_a_value,
    get_floor_rate,
    select_table,
    UNIT_EOUK,
)
from g2b.services.optimal_bid import (
    OptimalBidInput,
    find_optimal_bid,
)
from g2b.management.commands.simulate_historical import (
    load_excel_data,
    load_a_values,
    load_preliminary_prices,
    parse_amount,
    EXCEL_FILES,
    A_VALUES_JSON,
    PRELIM_PRICES_JSON,
    CONSTRUCTION_KEYWORDS,
)


class Command(BaseCommand):
    help = "BC-46: 하한율 미달 방지 시뮬레이션 (558건 나의방 데이터)"

    def handle(self, *args, **options):
        verbosity = options["verbosity"]

        # 1. 데이터 로드
        self.stdout.write("데이터 로드 중...")
        rows = load_excel_data(EXCEL_FILES)
        a_values = load_a_values(A_VALUES_JSON)
        prelim_prices = load_preliminary_prices(PRELIM_PRICES_JSON)
        self.stdout.write(
            f"  엑셀 {len(rows)}건, A값 {len(a_values)}건, "
            f"복수예비가격 {len(prelim_prices)}건"
        )

        # 2. 적격심사 대상 필터링
        eligible = []
        for row in rows:
            est_price = row["est_price"]
            det_price = row["det_price"]
            my_bid = row["my_bid"]

            # 추정가격/예정가격/투찰금액 필수
            if not est_price or est_price <= 0:
                continue
            if not det_price or det_price <= 0:
                continue
            if not my_bid or my_bid <= 0:
                continue

            # 공사구분
            work_cat = row.get("work_category", "")
            work_type = (
                WorkType.SPECIALTY
                if work_cat and not any(k in work_cat for k in CONSTRUCTION_KEYWORDS)
                else WorkType.CONSTRUCTION
            )

            # 테이블 라우팅
            routing_price = est_price
            try:
                table_type = select_table(routing_price, work_type)
            except ValueError:
                continue

            if table_type == TableType.OUT_OF_SCOPE:
                continue

            # A값
            bid_no = row["bid_no"]
            a_items = a_values.get(bid_no, AValueItems())
            try:
                a_value = calculate_a_value(a_items)
            except ValueError:
                a_value = 0

            if a_value >= det_price:
                continue

            eligible.append({
                "bid_no": bid_no,
                "est_price": est_price,
                "det_price": det_price,
                "my_bid": my_bid,
                "my_rank": row.get("my_rank"),
                "table_type": table_type,
                "work_type": work_type,
                "a_value": a_value,
                "has_a_value": bid_no in a_values,
                "has_prelim": bid_no in prelim_prices,
            })

        self.stdout.write(f"\n적격심사 대상: {len(eligible)}건")

        # 3. 하한율 미달 판정
        floor_fail = []
        floor_pass = []
        table_stats = defaultdict(lambda: {"total": 0, "fail": 0})

        for item in eligible:
            floor_rate = get_floor_rate(item["est_price"])
            scoring_ratio = (
                (item["my_bid"] - item["a_value"])
                / (item["det_price"] - item["a_value"])
            )
            ratio_pct = scoring_ratio * 100
            deficit_pct = float(floor_rate) - ratio_pct

            tbl = item["table_type"].value
            table_stats[tbl]["total"] += 1

            if ratio_pct < float(floor_rate):
                item["deficit_pct"] = deficit_pct
                floor_fail.append(item)
                table_stats[tbl]["fail"] += 1
            else:
                floor_pass.append(item)

        # 미달 구간 분류
        within_1pct = [f for f in floor_fail if f["deficit_pct"] <= 1.0]
        within_5pct = [f for f in floor_fail if 1.0 < f["deficit_pct"] <= 5.0]
        over_5pct = [f for f in floor_fail if f["deficit_pct"] > 5.0]

        n_total = len(eligible)
        n_fail = len(floor_fail)

        self.stdout.write(
            f"\n{'=' * 50}\n"
            f"=== 하한율 미달 방지 시뮬레이션 (BC-46) ===\n"
            f"{'=' * 50}\n"
        )
        self.stdout.write(f"적격심사 대상:    {n_total}건")
        self.stdout.write(
            f"하한율 미달:      {n_fail}건 ({n_fail / n_total * 100:.1f}%)"
        )
        self.stdout.write(f"  1% 이내 미달:   {len(within_1pct)}건")
        self.stdout.write(f"  1~5% 미달:      {len(within_5pct)}건")
        self.stdout.write(f"  5% 초과 미달:   {len(over_5pct)}건")

        # Level 1
        self.stdout.write(
            f"\n[Level 1] 경고 방지 가능: {n_fail}건 (100%)"
        )
        self.stdout.write(
            "  → 하한율+최소투찰가 표시만으로 사용자가 회피 가능"
        )

        # Level 2: 엔진 자동 방지
        # 실제 예정가격(det_price) 기준으로 추천 bid의 하한율 통과 여부 판정
        verifiable = [
            item for item in floor_fail
            if item["has_a_value"] and item["has_prelim"]
        ]
        auto_prevented = 0
        not_prevented = 0
        skipped = 0

        for item in verifiable:
            bid_no = item["bid_no"]
            prelim_raw = prelim_prices.get(bid_no, [])

            # 복수예비가격 파싱
            parsed_prices = []
            for p in prelim_raw:
                if isinstance(p, dict):
                    val = p.get("bsisPlnprc")
                    if val:
                        parsed = parse_amount(val)
                        if parsed and parsed > 0:
                            parsed_prices.append(parsed)
                elif isinstance(p, (int, float)):
                    parsed_prices.append(int(p))

            if len(parsed_prices) < 4:
                skipped += 1
                continue

            try:
                inp = OptimalBidInput(
                    preliminary_prices=parsed_prices,
                    a_value=item["a_value"],
                    table_type=item["table_type"],
                    presume_price=item["est_price"],
                )
                result = find_optimal_bid(inp)

                # 실제 예정가격 기준 하한율 체크
                a = item["a_value"]
                det = item["det_price"]
                floor_rate = get_floor_rate(item["est_price"])
                rec_ratio = (result.recommended_bid - a) / (det - a) * 100

                if rec_ratio >= float(floor_rate):
                    auto_prevented += 1
                else:
                    not_prevented += 1

                if verbosity >= 2:
                    status = "PASS" if rec_ratio >= float(floor_rate) else "FAIL"
                    self.stdout.write(
                        f"  [{status}] {bid_no}: "
                        f"추천={result.recommended_bid:,} "
                        f"추천ratio={rec_ratio:.4f}% "
                        f"하한율={floor_rate}%"
                    )
            except (ValueError, ZeroDivisionError) as e:
                skipped += 1
                if verbosity >= 2:
                    self.stdout.write(f"  [SKIP] {bid_no}: {e}")

        n_verified = auto_prevented + not_prevented
        if n_verified > 0:
            self.stdout.write(
                f"\n[Level 2] 엔진 자동 방지: "
                f"{auto_prevented}건 / {n_verified}건 검증 대상 "
                f"({auto_prevented / n_verified * 100:.1f}%)"
            )
        else:
            self.stdout.write("\n[Level 2] 엔진 자동 방지: 검증 대상 0건")
        self.stdout.write(
            "  → A값+복수예비가격 보유 건에서 엔진 추천 bid의 실제 예정가격 기준 하한율 통과"
        )
        self.stdout.write(f"  검증 가능:   {len(verifiable)}건 (A값+복수예비가격 둘 다 보유)")
        self.stdout.write(f"  자동 방지:   {auto_prevented}건 (추천 bid → 실제 예정가격 기준 하한율 통과)")
        self.stdout.write(f"  미방지:      {not_prevented}건")
        if skipped > 0:
            self.stdout.write(f"  건너뜀:      {skipped}건 (복수예비가격 <4개 또는 에러)")

        # TABLE별 통계
        self.stdout.write("\nTABLE별:")
        for tbl in sorted(table_stats):
            ts = table_stats[tbl]
            # TABLE별 엔진 자동 방지 건수
            tbl_verifiable = [
                item for item in floor_fail
                if item["table_type"].value == tbl
                and item["has_a_value"] and item["has_prelim"]
            ]
            self.stdout.write(
                f"  {tbl}: {ts['total']}건 중 "
                f"경고 {ts['fail']}건 / "
                f"자동 {len([v for v in tbl_verifiable])}건 검증 대상"
            )

        self.stdout.write(f"\n{'=' * 50}")
