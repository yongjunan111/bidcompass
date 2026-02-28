"""계약정보 수집 커맨드.

사용:
    python manage.py fetch_contracts --days 7
    python manage.py fetch_contracts --start 20260101 --end 20260131
"""

import asyncio
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from g2b.models import Contract, FetchLog
from g2b.services.g2b_client import fetch_pages


def parse_int(value) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def date_chunks(start: str, end: str, max_days: int = 30):
    """날짜 범위를 max_days 단위로 분할."""
    fmt = "%Y%m%d"
    s = datetime.strptime(start, fmt)
    e = datetime.strptime(end, fmt)
    while s <= e:
        chunk_end = min(s + timedelta(days=max_days - 1), e)
        yield s.strftime(fmt), chunk_end.strftime(fmt)
        s = chunk_end + timedelta(days=1)


def upsert_contracts(items: list[dict]) -> tuple[int, int]:
    """계약정보 upsert. (created, updated) 카운트 반환."""
    created = 0
    updated = 0
    for item in items:
        cntrct_no = item.get("cntrctNo", "")
        cntrct_sn = item.get("cntrctOrd", "") or ""
        if not cntrct_no:
            continue

        _, was_created = Contract.objects.update_or_create(
            cntrct_no=cntrct_no,
            cntrct_cncls_sn=cntrct_sn,
            defaults={
                "bid_ntce_no": item.get("bidNtceNo", "") or "",
                "cntrct_amt": parse_int(item.get("cntrctAmt")),
                "cntrct_cncls_de": item.get("cntrctCnclsDate", "") or "",
                "cntrct_biz_nm": item.get("rprsntCorpNm", "") or "",
                "cntrct_biz_no": item.get("rprsntCorpBizrno", "") or "",
                "raw_data": item,
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1
    return created, updated


async def _fetch_all_pages(start, end, callback=None):
    """API에서 모든 페이지를 async로 가져와 리스트로 반환."""
    params = {
        "cntrctCnclsBgnDate": start,
        "cntrctCnclsEndDate": end,
    }
    all_items = []
    async for items in fetch_pages("contracts", params, callback=callback):
        all_items.extend(items)
    return all_items


class Command(BaseCommand):
    help = "G2B 계약정보를 수집하여 DB에 적재합니다"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, help="최근 N일 수집")
        parser.add_argument("--start", type=str, help="시작일 (YYYYMMDD)")
        parser.add_argument("--end", type=str, help="종료일 (YYYYMMDD)")

    def handle(self, *args, **options):
        now = datetime.now()

        if options["start"] and options["end"]:
            start = options["start"]
            end = options["end"]
        else:
            days = options.get("days") or 7
            start = (now - timedelta(days=days)).strftime("%Y%m%d")
            end = now.strftime("%Y%m%d")

        self.stdout.write(f"계약정보 수집: {start} ~ {end}")

        for chunk_start, chunk_end in date_chunks(start, end):
            self.stdout.write(f"  청크: {chunk_start} ~ {chunk_end}")
            self._fetch_chunk(chunk_start, chunk_end)

        self.stdout.write(self.style.SUCCESS("계약정보 수집 완료"))

    def _fetch_chunk(self, start: str, end: str):
        log = FetchLog.objects.create(
            endpoint="contracts",
            date_from=start,
            date_to=end,
        )

        try:
            def on_page(page_no, fetched, total):
                self.stdout.write(f"    page {page_no}: {fetched}/{total}")

            all_items = asyncio.run(_fetch_all_pages(start, end, callback=on_page))
            created, updated = upsert_contracts(all_items)

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
