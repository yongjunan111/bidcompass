from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from g2b.models import (
    BidAnnouncement,
    BidApiAValue,
    BidApiCollectionLog,
    BidApiPrelimPrice,
    BidContract,
    BidResult,
)
from g2b.services.g2b_construction_client import (
    fetch_construction_a_value,
    fetch_construction_base_amount,
    fetch_construction_notices,
    fetch_construction_prelim_prices,
    fetch_construction_successful_bids,
)
from g2b.services.g2b_construction_sync import (
    PLACEHOLDER_CONTRACT_NO,
    PLACEHOLDER_PRELIM_SEQUENCE,
    bulk_upsert,
    is_eligible_notice_for_service,
    is_upcoming_notice,
    map_a_value_item,
    map_base_amount_to_placeholder_prelim,
    map_notice_to_announcement,
    map_notice_to_contract,
    map_prelim_price_item,
    map_successful_bid_to_result,
)


class Command(BaseCommand):
    help = '최근 건설공사 추천 대상 공고를 API로 수집해 현재 모델에 적재합니다. (개별 커맨드: fetch_announcements, fetch_winning_bids, fetch_contracts)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=1, help='최근 N일 조회 (기본 1)')
        parser.add_argument('--notice-limit', type=int, default=0, help='공고 최대 수집 건수')
        parser.add_argument('--result-limit', type=int, default=0, help='낙찰 최대 수집 건수')
        parser.add_argument(
            '--include-results',
            action='store_true',
            help='낙찰 결과도 함께 수집 (백테스트/사후 분석용)',
        )
        parser.add_argument(
            '--include-api-data',
            action='store_true',
            help='A값과 기초금액/예비가격도 함께 수집',
        )
        parser.add_argument(
            '--api-data-limit',
            type=int,
            default=50,
            help='부가 API 수집 최대 건수 (기본 50)',
        )
        parser.add_argument(
            '--force-api-data',
            action='store_true',
            help='기존 수집 로그가 있어도 A값/기초금액을 다시 수집',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 DB 적재 없이 API 응답과 매핑만 검증',
        )

    def handle(self, *args, **options):
        days = max(options['days'], 1)
        notice_limit = options['notice_limit'] or None
        include_results = options['include_results']
        result_limit = (options['result_limit'] or None) if include_results else None
        include_api_data = options['include_api_data']
        api_data_limit = max(options['api_data_limit'], 0)
        force_api_data = options['force_api_data']
        dry_run = options['dry_run']

        now = timezone.localtime()
        now_key = now.strftime('%Y%m%d%H%M')
        start = now - timedelta(days=days)
        start_datetime = start.strftime('%Y%m%d0000')
        end_datetime = now.strftime('%Y%m%d2359')

        self.stdout.write(
            f'건설공사 추천 대상 공고 동기화: {start_datetime} ~ {end_datetime}'
        )

        fetched_notice_items = fetch_construction_notices(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=notice_limit,
            server_filters=settings.G2B_SERVER_FILTERS['notice'],
            callback=lambda page_no, fetched, total: self.stdout.write(
                f'  공고 page {page_no}: {fetched}/{total}'
            ),
        )
        notice_items = [
            item for item in fetched_notice_items
            if is_eligible_notice_for_service(item) and is_upcoming_notice(item, now_key)
        ]

        notice_index = {
            (item.get('bidNtceNo', '') or '', item.get('bidNtceOrd', '') or ''): item
            for item in fetched_notice_items
        }
        announcement_rows = [map_notice_to_announcement(item) for item in notice_items]
        contract_rows = [map_notice_to_contract(item) for item in notice_items]
        result_rows: list[dict] = []
        if include_results:
            result_items = fetch_construction_successful_bids(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                limit=result_limit,
                server_filters=settings.G2B_SERVER_FILTERS['notice'],
                callback=lambda page_no, fetched, total: self.stdout.write(
                    f'  낙찰 page {page_no}: {fetched}/{total}'
                ),
            )
            result_rows = [
                map_successful_bid_to_result(
                    item,
                    notice_index.get((item.get('bidNtceNo', '') or '', item.get('bidNtceOrd', '') or '')),
                )
                for item in result_items
            ]

        self.stdout.write(
            f'  원본 공고 {len(fetched_notice_items):,}건 / 추천 대상 공고 {len(announcement_rows):,}건 / 계약성 공고 {len(contract_rows):,}건 / 낙찰 {len(result_rows):,}건'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run: DB에는 적재하지 않습니다.'))
            if announcement_rows:
                sample = announcement_rows[0]
                self.stdout.write(
                    f"  sample 공고: [{sample['bid_ntce_no']}] {sample['bid_ntce_nm']} / {sample['presume_price']}"
                )
            return

        with transaction.atomic():
            ann_created, ann_updated = bulk_upsert(
                BidAnnouncement,
                announcement_rows,
                unique_fields=['bid_ntce_no', 'bid_ntce_ord'],
            )
            contract_created, contract_updated = bulk_upsert(
                BidContract,
                contract_rows,
                unique_fields=['bid_ntce_no', 'bid_ntce_ord', 'contract_no'],
            )
            result_created, result_updated = bulk_upsert(
                BidResult,
                result_rows,
                unique_fields=[
                    'bid_ntce_no',
                    'bid_ntce_ord',
                    'company_bizno',
                    'bid_class_no',
                    'bid_progress_ord',
                ],
            )

        self.stdout.write(
            self.style.SUCCESS(
                '  적재 완료 '
                f'(공고 신규 {ann_created:,} / 갱신 {ann_updated:,}, '
                f'계약 신규 {contract_created:,} / 갱신 {contract_updated:,}, '
                f'낙찰 신규 {result_created:,} / 갱신 {result_updated:,})'
            )
        )

        if include_api_data:
            eligible_notice_items = notice_items[:api_data_limit]
            self._sync_supporting_api_data(
                eligible_notice_items,
                force_api_data=force_api_data,
            )

    def _sync_supporting_api_data(
        self,
        notice_items: list[dict],
        *,
        force_api_data: bool,
    ) -> None:
        if not notice_items:
            self.stdout.write('  부가 API 수집 대상이 없습니다.')
            return

        self.stdout.write(f'  A값/기초금액 수집 대상: {len(notice_items):,}건')

        a_ok = 0
        prelim_ok = 0
        errors = 0

        for index, item in enumerate(notice_items, start=1):
            bid_ntce_no = item.get('bidNtceNo', '') or ''
            bid_ntce_ord = item.get('bidNtceOrd', '') or ''
            log, _ = BidApiCollectionLog.objects.get_or_create(
                bid_ntce_no=bid_ntce_no,
                bid_ntce_ord=bid_ntce_ord,
            )

            if (
                not force_api_data
                and log.a_value_status == 'ok'
                and log.prelim_status == 'ok'
            ):
                continue

            self.stdout.write(f'    [{index}/{len(notice_items)}] {bid_ntce_no}-{bid_ntce_ord}')

            try:
                a_value_item = fetch_construction_a_value(bid_ntce_no)
                if a_value_item:
                    BidApiAValue.objects.update_or_create(
                        bid_ntce_no=bid_ntce_no,
                        bid_ntce_ord=bid_ntce_ord,
                        defaults=map_a_value_item(a_value_item),
                    )
                    log.a_value_status = 'ok'
                    a_ok += 1
                else:
                    log.a_value_status = 'empty'

                prelim_items = fetch_construction_prelim_prices(bid_ntce_no, bid_ntce_ord)
                if prelim_items:
                    BidApiPrelimPrice.objects.filter(
                        bid_ntce_no=bid_ntce_no,
                        bid_ntce_ord=bid_ntce_ord,
                    ).delete()
                    for prelim_item in prelim_items:
                        row = map_prelim_price_item(prelim_item)
                        BidApiPrelimPrice.objects.update_or_create(
                            bid_ntce_no=bid_ntce_no,
                            bid_ntce_ord=bid_ntce_ord,
                            sequence_no=row['sequence_no'],
                            defaults=row,
                        )
                    log.prelim_status = 'ok'
                    prelim_ok += 1
                else:
                    base_amount_item = fetch_construction_base_amount(bid_ntce_no)
                    if base_amount_item:
                        placeholder_row = map_base_amount_to_placeholder_prelim(base_amount_item)
                        BidApiPrelimPrice.objects.update_or_create(
                            bid_ntce_no=bid_ntce_no,
                            bid_ntce_ord=bid_ntce_ord,
                            sequence_no=PLACEHOLDER_PRELIM_SEQUENCE,
                            defaults=placeholder_row,
                        )
                        log.prelim_status = 'ok'
                        prelim_ok += 1
                    else:
                        log.prelim_status = 'empty'

                log.error_detail = ''
            except Exception as exc:
                errors += 1
                log.a_value_status = 'error'
                log.prelim_status = 'error'
                log.error_detail = str(exc)
                self.stderr.write(self.style.ERROR(f'      오류: {exc}'))

            log.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'  부가 API 완료 (A값 성공 {a_ok:,}건 / 기초금액·예비가격 성공 {prelim_ok:,}건 / 오류 {errors:,}건)'
            )
        )
