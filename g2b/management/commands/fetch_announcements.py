"""입찰공고정보 수집 커맨드.

사용:
    python manage.py fetch_announcements --days 7
    python manage.py fetch_announcements --start 20260101 --end 20260131
"""

import asyncio
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from g2b.models import BidAnnouncement, FetchLog
from g2b.services.g2b_client import fetch_pages


def parse_int(value) -> int | None:
    """문자열을 int로 변환. 빈 값이면 None."""
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def upsert_announcements(items: list[dict]) -> tuple[int, int]:
    """입찰공고 upsert. (created, updated) 카운트 반환."""
    created = 0
    updated = 0
    for item in items:
        ntce_no = item.get("bidNtceNo", "")
        ntce_ord = item.get("bidNtceOrd", "")
        if not ntce_no:
            continue

        _, was_created = BidAnnouncement.objects.update_or_create(
            bid_ntce_no=ntce_no,
            bid_ntce_ord=ntce_ord,
            defaults={
                "ntce_instt_nm": item.get("ntceInsttNm", "") or "",
                "bid_ntce_nm": item.get("bidNtceNm", "") or "",
                "presmpt_prce": parse_int(item.get("presmptPrce")),
                "bss_amt": parse_int(item.get("asignBdgtAmt")),
                "bidwin_dcn_mthd_nm": item.get("bidwinrDcsnMthdNm", "") or "",
                "bid_ntce_dt": item.get("bidNtceDate", "") or "",
                "bid_clse_dt": item.get("bidClseDate", "") or "",
                "raw_data": item,
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1
    return created, updated


def date_chunks(start: str, end: str, max_days: int = 30):
    """날짜 범위를 max_days 단위로 분할. (chunk_start, chunk_end) 생성."""
    fmt = "%Y%m%d"
    s = datetime.strptime(start, fmt)
    e = datetime.strptime(end, fmt)
    while s <= e:
        chunk_end = min(s + timedelta(days=max_days - 1), e)
        yield s.strftime(fmt), chunk_end.strftime(fmt)
        s = chunk_end + timedelta(days=1)


async def _fetch_all_pages(start, end, callback=None):
    """API에서 모든 페이지를 async로 가져와 리스트로 반환."""
    params = {
        "bidNtceBgnDt": f"{start}0000",
        "bidNtceEndDt": f"{end}2359",
    }
    all_items = []
    async for items in fetch_pages("announcements", params, callback=callback):
        all_items.extend(items)
    return all_items


class Command(BaseCommand):
    help = "G2B 입찰공고정보를 수집하여 DB에 적재합니다"

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

        self.stdout.write(f"입찰공고 수집: {start} ~ {end}")

        for chunk_start, chunk_end in date_chunks(start, end):
            self.stdout.write(f"  청크: {chunk_start} ~ {chunk_end}")
            self._fetch_chunk(chunk_start, chunk_end)

        self.stdout.write(self.style.SUCCESS("입찰공고 수집 완료"))

    def _fetch_chunk(self, start: str, end: str):
        log = FetchLog.objects.create(
            endpoint="announcements",
            date_from=start,
            date_to=end,
        )

        try:
            def on_page(page_no, fetched, total):
                self.stdout.write(f"    page {page_no}: {fetched}/{total}")

            # async로 API 호출만 수행
            all_items = asyncio.run(_fetch_all_pages(start, end, callback=on_page))

            # sync로 DB 적재
            created, updated = upsert_announcements(all_items)

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
