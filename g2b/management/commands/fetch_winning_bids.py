"""낙찰정보 수집 커맨드.

낙찰정보 API는 1일 범위만 허용하므로 일별로 반복 호출한다.

사용:
    python manage.py fetch_winning_bids --days 3
    python manage.py fetch_winning_bids --date 20260225
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.utils import timezone

from g2b.models import FetchLog, SuccessfulBid
from g2b.services.g2b_client import fetch_pages


def parse_int(value) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_decimal(value) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def upsert_winning_bids(items: list[dict]) -> tuple[int, int]:
    """낙찰정보 upsert. (created, updated) 카운트 반환."""
    created = 0
    updated = 0
    for item in items:
        ntce_no = item.get("bidNtceNo", "")
        ntce_ord = item.get("bidNtceOrd", "") or ""
        bizno = item.get("bidprcCorpBizrno", "") or ""
        if not ntce_no:
            continue

        _, was_created = SuccessfulBid.objects.update_or_create(
            bid_ntce_no=ntce_no,
            bid_ntce_ord=ntce_ord,
            prcbdr_bizno=bizno,
            defaults={
                "prcbdr_nm": item.get("bidprcCorpNm", "") or "",
                "rsrvtn_prce": parse_int(item.get("rsrvtnPrce")),
                "bss_amt": parse_int(item.get("bssAmt")),
                "presmpt_prce": parse_int(item.get("presmptPrce")),
                "bidprc_amt": parse_int(item.get("bidprcAmt")),
                "bidprc_rt": parse_decimal(item.get("bidprcRt")),
                "sucsf_lwstlmt_rt": parse_decimal(item.get("sucsfLwstlmtRt")),
                "sucsf_yn": item.get("sucsfYn", "") or "",
                "openg_rank": parse_int(item.get("opengRank")),
                "dqlfctn_rsn": item.get("dqlfctnRsn", "") or "",
                "raw_data": item,
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1
    return created, updated


async def _fetch_all_pages(date_str, callback=None):
    """API에서 1일치 모든 페이지를 async로 가져와 리스트로 반환."""
    params = {
        "opengBgnDt": f"{date_str}0000",
        "opengEndDt": f"{date_str}2359",
        "bsnsDivCd": "3",  # 공사
    }
    all_items = []
    async for items in fetch_pages("winning_bids", params, callback=callback):
        all_items.extend(items)
    return all_items


class Command(BaseCommand):
    help = "G2B 낙찰정보를 수집하여 DB에 적재합니다 (1일 단위 반복)"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, help="최근 N일 수집")
        parser.add_argument("--date", type=str, help="특정일 수집 (YYYYMMDD)")

    def handle(self, *args, **options):
        now = datetime.now()

        if options.get("date"):
            dates = [options["date"]]
        else:
            days = options.get("days") or 3
            dates = [
                (now - timedelta(days=i)).strftime("%Y%m%d")
                for i in range(days, 0, -1)
            ]

        self.stdout.write(f"낙찰정보 수집: {len(dates)}일 ({dates[0]} ~ {dates[-1]})")

        for date_str in dates:
            self.stdout.write(f"  {date_str} 수집 중...")
            self._fetch_day(date_str)

        self.stdout.write(self.style.SUCCESS("낙찰정보 수집 완료"))

    def _fetch_day(self, date_str: str):
        log = FetchLog.objects.create(
            endpoint="winning_bids",
            date_from=date_str,
            date_to=date_str,
        )

        try:
            def on_page(page_no, fetched, total):
                self.stdout.write(f"    page {page_no}: {fetched}/{total}")

            all_items = asyncio.run(_fetch_all_pages(date_str, callback=on_page))
            created, updated = upsert_winning_bids(all_items)

            log.status = "success"
            log.total_count = len(all_items)
            log.fetched_count = len(all_items)
            log.created_count = created
            log.updated_count = updated

        except Exception as e:
            log.status = "error"
            log.error_message = str(e)
            self.stderr.write(self.style.ERROR(f"오류: {e}"))
            created, updated = 0, 0

        log.finished_at = timezone.now()
        log.save()

        self.stdout.write(
            f"  결과: 수집={log.fetched_count} 신규={created} 갱신={updated}"
        )
