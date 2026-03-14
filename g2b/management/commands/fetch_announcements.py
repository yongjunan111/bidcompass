"""건설공사 입찰공고 수집 (Pipeline 1).

서비스용 신규 공고를 수집하여 BidAnnouncement + BidContract(NOTICE placeholder)에 적재하고,
각 공고의 A값 + 기초금액을 사전 수집합니다.

사용:
    python manage.py fetch_announcements --days 2
    python manage.py fetch_announcements --days 1 --dry-run
"""

from __future__ import annotations

import json
import time
from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from g2b.models import BidAnnouncement, BidApiAValue, BidApiPrelimPrice, BidContract
from g2b.services.g2b_construction_client import (
    REQUEST_DELAY,
    fetch_construction_a_value,
    fetch_construction_base_amount,
    fetch_construction_notices,
)
from g2b.services.g2b_construction_sync import (
    PLACEHOLDER_PRELIM_SEQUENCE,
    bulk_upsert,
    is_eligible_notice_for_service,
    is_upcoming_notice,
    map_a_value_item,
    map_base_amount_to_placeholder_prelim,
    map_notice_to_announcement,
    map_notice_to_contract,
    ntce_key,
    resolve_server_filters,
)


RAW_NOTICES_DIR = Path(__file__).resolve().parents[3] / "data" / "collected" / "api_raw" / "notices"


class Command(BaseCommand):
    help = '건설공사 추천 대상 공고를 수집하고 A값/기초금액을 사전 수집합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=1, help='최근 N일 조회 (기본 1)')
        parser.add_argument('--limit', type=int, default=0, help='최대 수집 건수')
        parser.add_argument('--dry-run', action='store_true', help='DB 적재 없이 검증만')
        parser.add_argument('--skip-detail', action='store_true', help='A값/기초금액 수집 생략')
        parser.add_argument('--no-server-filter', action='store_true', help='서버사이드 필터 비활성화 (디버깅용)')

    def handle(self, *args, **options):
        days = max(options['days'], 1)
        limit = options['limit'] or None
        dry_run = options['dry_run']
        skip_detail = options['skip_detail']
        no_server_filter = options['no_server_filter']

        server_filters = resolve_server_filters(no_server_filter, self.stdout)

        now = timezone.localtime()
        now_key = now.strftime('%Y%m%d%H%M')
        start = now - timedelta(days=days)
        start_datetime = start.strftime('%Y%m%d0000')
        end_datetime = now.strftime('%Y%m%d2359')

        self.stdout.write(f'공고 수집: {start_datetime} ~ {end_datetime}')

        fetched_items = fetch_construction_notices(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=limit,
            server_filters=server_filters,
            callback=lambda page_no, fetched, total: self.stdout.write(
                f'  page {page_no}: {fetched}/{total}'
            ),
        )

        start_key = start_datetime[:8]
        end_key = end_datetime[:8]
        RAW_NOTICES_DIR.mkdir(parents=True, exist_ok=True)
        raw_path = RAW_NOTICES_DIR / f"notices_{start_key}_{end_key}.json"
        raw_path.write_text(json.dumps(fetched_items, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(f'  JSON 원본 저장: {raw_path}')

        eligible_items = [
            item for item in fetched_items
            if is_eligible_notice_for_service(item) and is_upcoming_notice(item, now_key)
        ]

        announcement_rows = [map_notice_to_announcement(item) for item in eligible_items]
        contract_rows = [map_notice_to_contract(item) for item in eligible_items]

        self.stdout.write(
            f'  원본 {len(fetched_items):,}건 / 추천 대상 {len(eligible_items):,}건'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run: DB에는 적재하지 않습니다.'))
            if announcement_rows:
                sample = announcement_rows[0]
                self.stdout.write(
                    f"  sample: [{sample['bid_ntce_no']}] {sample['bid_ntce_nm']} / {sample['presume_price']}"
                )
            return

        with transaction.atomic():
            ann_created, ann_updated = bulk_upsert(
                BidAnnouncement,
                announcement_rows,
                unique_fields=['bid_ntce_no', 'bid_ntce_ord'],
            )
            con_created, con_updated = bulk_upsert(
                BidContract,
                contract_rows,
                unique_fields=['bid_ntce_no', 'bid_ntce_ord', 'contract_no'],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'  적재 완료 (공고 신규 {ann_created:,} / 갱신 {ann_updated:,}, '
                f'계약 신규 {con_created:,} / 갱신 {con_updated:,})'
            )
        )

        if not skip_detail:
            self._collect_a_values_and_base_amounts(eligible_items)

    def _collect_a_values_and_base_amounts(self, eligible_items):
        if not eligible_items:
            return

        ntce_nos = sorted({item.get('bidNtceNo', '') for item in eligible_items})
        a_collected = set(
            BidApiAValue.objects.filter(
                bid_ntce_no__in=ntce_nos,
            ).values_list('bid_ntce_no', 'bid_ntce_ord')
        )
        base_collected = set(
            BidApiPrelimPrice.objects.filter(
                bid_ntce_no__in=ntce_nos,
                sequence_no=PLACEHOLDER_PRELIM_SEQUENCE,
            ).values_list('bid_ntce_no', 'bid_ntce_ord')
        )
        fully_collected = a_collected & base_collected

        targets = [
            item for item in eligible_items
            if ntce_key(item) not in fully_collected
        ]

        if not targets:
            self.stdout.write('  A값/기초금액: 전부 수집 완료 (스킵)')
            return

        self.stdout.write(
            f'  A값/기초금액 수집: {len(targets):,}건'
            f' (A값+기초금액 모두 수집 {len(fully_collected):,}건 스킵)'
        )

        a_value_rows = []
        base_amount_rows = []
        errors = 0

        for i, item in enumerate(targets):
            bid_ntce_no = item.get('bidNtceNo', '')
            bid_ntce_ord = item.get('bidNtceOrd', '')

            # A값 수집
            a_status = 'checked_missing'
            try:
                a_value_item = fetch_construction_a_value(bid_ntce_no, bid_ntce_ord)
                if a_value_item:
                    a_value_rows.append(map_a_value_item(a_value_item))
                    a_status = 'confirmed'
            except Exception as e:
                a_status = 'pending'
                errors += 1
                self.stderr.write(f'  A값 에러 [{bid_ntce_no}]: {e}')

            time.sleep(REQUEST_DELAY)

            # 기초금액 수집
            base_status = 'checked_missing'
            try:
                base_amount_item = fetch_construction_base_amount(bid_ntce_no, bid_ntce_ord)
                if base_amount_item:
                    base_amount_rows.append(
                        map_base_amount_to_placeholder_prelim(base_amount_item)
                    )
                    base_status = 'confirmed'
            except Exception as e:
                base_status = 'pending'
                errors += 1
                self.stderr.write(f'  기초금액 에러 [{bid_ntce_no}]: {e}')

            time.sleep(REQUEST_DELAY)

            # BidAnnouncement 상태 업데이트
            BidAnnouncement.objects.filter(
                bid_ntce_no=bid_ntce_no,
                bid_ntce_ord=bid_ntce_ord,
            ).update(
                a_value_status=a_status,
                base_amount_status=base_status,
                a_value_checked_at=timezone.now(),
                base_amount_checked_at=timezone.now(),
            )

            if (i + 1) % 50 == 0:
                self.stdout.write(f'    진행: {i + 1}/{len(targets)}')

        with transaction.atomic():
            a_created, a_updated = bulk_upsert(
                BidApiAValue,
                a_value_rows,
                unique_fields=['bid_ntce_no', 'bid_ntce_ord'],
            )
            p_created, p_updated = bulk_upsert(
                BidApiPrelimPrice,
                base_amount_rows,
                unique_fields=['bid_ntce_no', 'bid_ntce_ord', 'sequence_no'],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'  A값 (신규 {a_created:,} / 갱신 {a_updated:,}), '
                f'기초금액 (신규 {p_created:,} / 갱신 {p_updated:,})'
                + (f', 에러 {errors}건' if errors else '')
            )
        )
