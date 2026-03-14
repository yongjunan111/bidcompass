"""건설공사 낙찰결과 수집 (Pipeline 2a).

낙찰 결과를 수집하고, notice enrichment(presume_price, success_lowest_rate)를 위해
BidAnnouncement DB를 우선 조회한 뒤 누락건만 API로 보충합니다.

사용:
    python manage.py fetch_winning_bids --days 3
    python manage.py fetch_winning_bids --days 1 --dry-run
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from g2b.models import BidAnnouncement, BidResult
from g2b.services.g2b_construction_client import (
    fetch_construction_notices,
    fetch_construction_successful_bids,
)
from g2b.services.g2b_construction_sync import (
    bulk_upsert,
    map_successful_bid_to_result,
    ntce_key,
    resolve_server_filters,
)


RAW_WINNING_BIDS_DIR = Path(__file__).resolve().parents[3] / "data" / "collected" / "api_raw" / "winning_bids"


class Command(BaseCommand):
    help = '건설공사 낙찰 결과를 수집하여 BidResult에 적재합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=3, help='최근 N일 조회 (기본 3)')
        parser.add_argument('--limit', type=int, default=0, help='최대 수집 건수')
        parser.add_argument('--dry-run', action='store_true', help='DB 적재 없이 검증만')
        parser.add_argument('--no-server-filter', action='store_true', help='서버사이드 필터 비활성화 (디버깅용)')

    def handle(self, *args, **options):
        days = max(options['days'], 1)
        limit = options['limit'] or None
        dry_run = options['dry_run']
        no_server_filter = options['no_server_filter']

        server_filters = resolve_server_filters(no_server_filter, self.stdout)

        now = timezone.localtime()
        start = now - timedelta(days=days)
        start_datetime = start.strftime('%Y%m%d0000')
        end_datetime = now.strftime('%Y%m%d2359')

        self.stdout.write(f'낙찰결과 수집: {start_datetime} ~ {end_datetime}')

        result_items = fetch_construction_successful_bids(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=limit,
            server_filters=server_filters,
            callback=lambda page_no, fetched, total: self.stdout.write(
                f'  낙찰 page {page_no}: {fetched}/{total}'
            ),
        )

        start_key = start_datetime[:8]
        end_key = end_datetime[:8]
        RAW_WINNING_BIDS_DIR.mkdir(parents=True, exist_ok=True)
        raw_path = RAW_WINNING_BIDS_DIR / f"winning_bids_{start_key}_{end_key}.json"
        raw_path.write_text(json.dumps(result_items, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(f'  JSON 원본 저장: {raw_path}')

        if not result_items:
            self.stdout.write('  낙찰 결과 없음')
            return

        # Notice enrichment: DB 우선 조회 → 누락건만 API 보충
        ntce_keys = {ntce_key(item) for item in result_items}
        ntce_nos = sorted({k[0] for k in ntce_keys})

        # Step 1: DB에서 BidAnnouncement 조회
        db_notices = BidAnnouncement.objects.filter(
            bid_ntce_no__in=ntce_nos,
        ).values('bid_ntce_no', 'bid_ntce_ord', 'presume_price', 'success_lowest_rate')

        notice_index: dict[tuple[str, str], dict] = {}
        for row in db_notices:
            key = (row['bid_ntce_no'], row['bid_ntce_ord'])
            notice_index[key] = {
                'presmptPrce': row['presume_price'],
                'sucsfbidLwltRate': row['success_lowest_rate'],
            }

        # Step 2: DB에 없는 공고만 API로 보충
        missing_keys = ntce_keys - set(notice_index.keys())
        if missing_keys:
            self.stdout.write(f'  notice enrichment: DB {len(notice_index)}건, API 보충 {len(missing_keys)}건')
            api_notice_items = fetch_construction_notices(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                callback=lambda page_no, fetched, total: self.stdout.write(
                    f'  공고 page {page_no}: {fetched}/{total}'
                ),
            )
            enrichment_path = RAW_WINNING_BIDS_DIR / f"notices_enrichment_{start_key}_{end_key}.json"
            enrichment_path.write_text(json.dumps(api_notice_items, ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(f'  JSON 원본 저장: {enrichment_path}')
            for item in api_notice_items:
                key = ntce_key(item)
                if key in missing_keys:
                    notice_index[key] = item
                    missing_keys.discard(key)
                    if not missing_keys:
                        break
        else:
            self.stdout.write(f'  notice enrichment: DB에서 전부 조회 ({len(notice_index)}건)')

        # 매핑
        result_rows = [
            map_successful_bid_to_result(item, notice_index.get(ntce_key(item)))
            for item in result_items
        ]

        self.stdout.write(f'  낙찰결과 {len(result_rows):,}건')

        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run: DB에는 적재하지 않습니다.'))
            if result_rows:
                sample = result_rows[0]
                self.stdout.write(
                    f"  sample: [{sample['bid_ntce_no']}] {sample['company_nm']} / rate={sample['bid_rate']}"
                )
            return

        with transaction.atomic():
            created, updated = bulk_upsert(
                BidResult,
                result_rows,
                unique_fields=[
                    'bid_ntce_no', 'bid_ntce_ord', 'company_bizno',
                    'bid_class_no', 'bid_progress_ord',
                ],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'  적재 완료 (신규 {created:,} / 갱신 {updated:,})'
            )
        )
