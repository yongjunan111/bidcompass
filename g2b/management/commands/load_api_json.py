"""JSON 원본에서 A값 + 복수예비가격을 DB에 재적재.

data/collected/api_raw/ 디렉토리의 JSON 파일을 읽어 DB에 적재한다.
DB 손실 시 복구용.

사용:
    python manage.py load_api_json                    # 전체 재적재
    python manage.py load_api_json --type a_value     # A값만
    python manage.py load_api_json --type prelim      # 복수예비가격만
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from g2b.models import BidApiAValue, BidApiPrelimPrice
from g2b.services.g2b_client import extract_items

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "collected" / "api_raw"
RAW_A_VALUE_DIR = RAW_DIR / "a_values"
RAW_PRELIM_DIR = RAW_DIR / "prelim_prices"

A_VALUE_API_TO_MODEL = {
    "npnInsrprm": "national_pension",
    "mrfnHealthInsrprm": "health_insurance",
    "rtrfundNon": "retirement_mutual_aid",
    "odsnLngtrmrcprInsrprm": "long_term_care",
    "sftyMngcst": "occupational_safety",
    "sftyChckMngcst": "safety_management",
    "qltyMngcst": "quality_management",
}


def parse_api_int(val) -> int:
    if val is None:
        return 0
    s = str(val).strip()
    if not s:
        return 0
    return int(float(s))


class Command(BaseCommand):
    help = "JSON 원본에서 A값 + 복수예비가격을 DB에 재적재"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=["a_value", "prelim", "all"],
            default="all",
            help="적재 대상 (기본: all)",
        )

    def handle(self, *args, **options):
        load_type = options["type"]

        if load_type in ("a_value", "all"):
            self._load_a_values()
        if load_type in ("prelim", "all"):
            self._load_prelim_prices()

    def _load_a_values(self):
        if not RAW_A_VALUE_DIR.exists():
            self.stdout.write(self.style.WARNING(f"디렉토리 없음: {RAW_A_VALUE_DIR}"))
            return

        files = sorted(RAW_A_VALUE_DIR.glob("*.json"))
        self.stdout.write(f"A값 JSON 파일: {len(files)}개")

        loaded = 0
        for f in files:
            ntce_no, ntce_ord = f.stem.rsplit("_", 1)
            data = json.loads(f.read_text(encoding="utf-8"))
            items = extract_items(data)
            if not items:
                continue

            item = items[0]
            model_fields = {}
            for api_field, model_field in A_VALUE_API_TO_MODEL.items():
                model_fields[model_field] = parse_api_int(item.get(api_field))

            BidApiAValue.objects.update_or_create(
                bid_ntce_no=ntce_no,
                bid_ntce_ord=ntce_ord,
                defaults={
                    **model_fields,
                    "price_decision_method": item.get("prearngPrceDcsnMthdNm", ""),
                },
            )
            loaded += 1

        self.stdout.write(self.style.SUCCESS(f"A값 적재 완료: {loaded}건"))

    def _load_prelim_prices(self):
        if not RAW_PRELIM_DIR.exists():
            self.stdout.write(self.style.WARNING(f"디렉토리 없음: {RAW_PRELIM_DIR}"))
            return

        files = sorted(RAW_PRELIM_DIR.glob("*.json"))
        self.stdout.write(f"복수예비가격 JSON 파일: {len(files)}개")

        loaded = 0
        for f in files:
            ntce_no, ntce_ord = f.stem.rsplit("_", 1)
            data = json.loads(f.read_text(encoding="utf-8"))
            items = extract_items(data)
            if not items:
                continue

            BidApiPrelimPrice.objects.filter(
                bid_ntce_no=ntce_no,
                bid_ntce_ord=ntce_ord,
            ).delete()

            objs = []
            for idx, item in enumerate(items, 1):
                objs.append(BidApiPrelimPrice(
                    bid_ntce_no=ntce_no,
                    bid_ntce_ord=ntce_ord,
                    sequence_no=idx,
                    basis_planned_price=parse_api_int(item.get("bsisPlnprc")),
                    is_drawn=item.get("drwtYn") == "Y",
                    draw_count=parse_api_int(item.get("drwtNum")),
                    planned_price=parse_api_int(item.get("plnprc")),
                    base_amount=parse_api_int(item.get("bssamt")),
                ))
            BidApiPrelimPrice.objects.bulk_create(objs)
            loaded += 1

        self.stdout.write(self.style.SUCCESS(f"복수예비가격 적재 완료: {loaded}건"))
