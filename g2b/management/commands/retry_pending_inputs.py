"""BC-61: A값/기초금액 미확정 공고 재확인 배치.

개찰 전이면서 A값 또는 기초금액이 pending인 공고를 재조회하여
confirmed로 전환한다. lookback 날짜에 묶이지 않고
upcoming + unresolved 조건으로 대상을 잡는다.

사용:
    python manage.py retry_pending_inputs
    python manage.py retry_pending_inputs --limit 100
    python manage.py retry_pending_inputs --dry-run
"""

from __future__ import annotations

import time

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from g2b.models import BidAnnouncement, BidApiAValue, BidApiPrelimPrice, BidContract
from g2b.services.g2b_construction_client import (
    REQUEST_DELAY,
    fetch_construction_a_value,
    fetch_construction_base_amount,
)
from g2b.services.g2b_construction_sync import (
    PLACEHOLDER_PRELIM_SEQUENCE,
    bulk_upsert,
    map_a_value_item,
    map_base_amount_to_placeholder_prelim,
)


class Command(BaseCommand):
    help = 'A값/기초금액 미확정 공고를 재조회하여 상태를 업데이트합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=500, help='최대 재확인 건수 (기본 500)')
        parser.add_argument('--dry-run', action='store_true', help='DB 적재 없이 대상만 확인')

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        now = timezone.localtime()
        today_key = now.strftime('%Y%m%d')

        # 대상: pending + 개찰일 미경과
        # BidContract의 openg_date(YYYYMMDD)가 오늘 이후인 공고
        # openg_date가 없거나 빈값이면 upcoming으로 간주
        pending_announcements = (
            BidAnnouncement.objects.filter(
                Q(a_value_status__in=['pending', 'checked_missing'])
                | Q(base_amount_status__in=['pending', 'checked_missing']),
            )
            .exclude(presume_price__isnull=True)
            .exclude(presume_price=0)
            .order_by('-created_at')[:limit * 2]  # 여유분
        )

        # bulk prefetch: 개찰일 판정용 계약 정보
        ann_keys = [(a.bid_ntce_no, a.bid_ntce_ord) for a in pending_announcements]
        ann_ntce_nos = sorted({k[0] for k in ann_keys})
        contract_map: dict[tuple[str, str], BidContract] = {}
        for c in BidContract.objects.filter(
            bid_ntce_no__in=ann_ntce_nos,
        ).order_by('-created_at'):
            key = (c.bid_ntce_no, c.bid_ntce_ord)
            if key not in contract_map:
                contract_map[key] = c

        # 개찰일 필터
        targets = []
        expired_count = 0
        for ann in pending_announcements:
            contract = contract_map.get((ann.bid_ntce_no, ann.bid_ntce_ord))

            # 개찰일 미경과 판정
            openg_date = contract.openg_date if contract else ''
            if openg_date and openg_date < today_key:
                # 개찰일 경과 → error로 전환
                updates = {}
                if ann.a_value_status in ('pending', 'checked_missing'):
                    updates['a_value_status'] = 'error'
                if ann.base_amount_status in ('pending', 'checked_missing'):
                    updates['base_amount_status'] = 'error'
                if updates and not dry_run:
                    BidAnnouncement.objects.filter(pk=ann.pk).update(**updates)
                expired_count += 1
                continue

            targets.append(ann)
            if len(targets) >= limit:
                break

        self.stdout.write(
            f'재확인 대상: {len(targets)}건 (개찰 경과 → error: {expired_count}건)'
        )

        if not targets:
            self.stdout.write('재확인 대상 없음')
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run: 실제 API 호출 없이 종료'))
            for ann in targets[:5]:
                self.stdout.write(
                    f'  [{ann.bid_ntce_no}] A={ann.a_value_status} base={ann.base_amount_status}'
                )
            return

        # 재조회 실행
        a_value_rows = []
        base_amount_rows = []
        confirmed_a = 0
        confirmed_base = 0
        errors = 0

        for i, ann in enumerate(targets):
            a_status = ann.a_value_status
            base_status = ann.base_amount_status

            # A값 재조회 (pending 또는 checked_missing인 경우)
            if ann.a_value_status in ('pending', 'checked_missing'):
                a_status = 'checked_missing'
                try:
                    a_item = fetch_construction_a_value(
                        ann.bid_ntce_no, ann.bid_ntce_ord,
                    )
                    if a_item:
                        a_value_rows.append(map_a_value_item(a_item))
                        a_status = 'confirmed'
                        confirmed_a += 1
                except Exception as e:
                    a_status = 'pending'
                    errors += 1
                    self.stderr.write(f'  A값 에러 [{ann.bid_ntce_no}]: {e}')

                time.sleep(REQUEST_DELAY)

            # 기초금액 재조회 (pending 또는 checked_missing인 경우)
            if ann.base_amount_status in ('pending', 'checked_missing'):
                base_status = 'checked_missing'
                try:
                    base_item = fetch_construction_base_amount(
                        ann.bid_ntce_no, ann.bid_ntce_ord,
                    )
                    if base_item:
                        base_amount_rows.append(
                            map_base_amount_to_placeholder_prelim(base_item)
                        )
                        base_status = 'confirmed'
                        confirmed_base += 1
                except Exception as e:
                    base_status = 'pending'
                    errors += 1
                    self.stderr.write(f'  기초금액 에러 [{ann.bid_ntce_no}]: {e}')

                time.sleep(REQUEST_DELAY)

            # 상태 업데이트
            BidAnnouncement.objects.filter(pk=ann.pk).update(
                a_value_status=a_status,
                base_amount_status=base_status,
                a_value_checked_at=timezone.now(),
                base_amount_checked_at=timezone.now(),
            )

            if (i + 1) % 50 == 0:
                self.stdout.write(f'  진행: {i + 1}/{len(targets)}')

        # DB 적재
        if a_value_rows:
            bulk_upsert(
                BidApiAValue,
                a_value_rows,
                unique_fields=['bid_ntce_no', 'bid_ntce_ord'],
            )
        if base_amount_rows:
            bulk_upsert(
                BidApiPrelimPrice,
                base_amount_rows,
                unique_fields=['bid_ntce_no', 'bid_ntce_ord', 'sequence_no'],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'재확인 완료: A값 {confirmed_a}건 / 기초금액 {confirmed_base}건 confirmed'
                + (f', 에러 {errors}건' if errors else '')
            )
        )
