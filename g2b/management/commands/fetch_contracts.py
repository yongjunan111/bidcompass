"""건설공사 계약정보 수집 (Pipeline 2b).

범용 계약 API(getDataSetOpnStdCntrctInfo)에서 계약 데이터를 가져오고,
BidAnnouncement에 존재하는 건설공사 공고만 필터링하여 BidContract에 적재합니다.

사용:
    python manage.py fetch_contracts --days 7
    python manage.py fetch_contracts --days 3 --dry-run
"""

from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from g2b.models import BidAnnouncement, BidContract
from g2b.services.g2b_construction_client import fetch_construction_contracts
from g2b.services.g2b_construction_sync import (
    bulk_upsert,
    map_contract_item_to_bid_contract,
    ntce_key,
)


class Command(BaseCommand):
    help = '건설공사 계약정보를 범용 API에서 수집하여 BidContract에 적재합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='최근 N일 조회 (기본 7)')
        parser.add_argument('--limit', type=int, default=0, help='최대 수집 건수')
        parser.add_argument('--dry-run', action='store_true', help='DB 적재 없이 검증만')

    def handle(self, *args, **options):
        days = max(options['days'], 1)
        limit = options['limit'] or None
        dry_run = options['dry_run']

        now = timezone.localtime()
        start = now - timedelta(days=days)
        start_date = start.strftime('%Y%m%d')
        end_date = now.strftime('%Y%m%d')

        self.stdout.write(f'계약정보 수집: {start_date} ~ {end_date}')

        fetched_items = fetch_construction_contracts(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            callback=lambda page_no, fetched, total: self.stdout.write(
                f'  page {page_no}: {fetched}/{total}'
            ),
        )

        if not fetched_items:
            self.stdout.write('  계약 데이터 없음')
            return

        # 1차 필터: 공사만 (물품/용역 제외)
        construction_items = [
            item for item in fetched_items
            if (item.get('bsnsDivNm', '') or '').strip() == '공사'
        ]

        # 2차 필터: (bid_ntce_no, bid_ntce_ord) 튜플이 BidAnnouncement에 존재하는 건만
        candidate_nos = sorted({ntce_key(item)[0] for item in construction_items})
        existing_keys = set(
            BidAnnouncement.objects.filter(
                bid_ntce_no__in=candidate_nos,
            ).values_list('bid_ntce_no', 'bid_ntce_ord')
        )

        filtered_items = [
            item for item in construction_items
            if ntce_key(item) in existing_keys
        ]

        contract_rows = [map_contract_item_to_bid_contract(item) for item in filtered_items]

        self.stdout.write(
            f'  원본 {len(fetched_items):,}건 / 공사 {len(construction_items):,}건 / 건설공사 필터 통과 {len(filtered_items):,}건'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run: DB에는 적재하지 않습니다.'))
            if contract_rows:
                sample = contract_rows[0]
                self.stdout.write(
                    f"  sample: [{sample['bid_ntce_no']}] {sample['bid_ntce_nm']} / "
                    f"contract_no={sample['contract_no']} / amt={sample['contract_amt']}"
                )
            return

        with transaction.atomic():
            created, updated = bulk_upsert(
                BidContract,
                contract_rows,
                unique_fields=['bid_ntce_no', 'bid_ntce_ord', 'contract_no'],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'  적재 완료 (신규 {created:,} / 갱신 {updated:,})'
            )
        )
