"""BC-61 Phase C: A값/기초금액 status 일괄 backfill.

BidApiAValue 또는 BidApiPrelimPrice 레코드가 존재하는 공고의
a_value_status / base_amount_status를 'confirmed'로 업데이트한다.

배경:
    canonical source = 레코드 존재 여부 (record existence).
    status 필드는 배치 메타데이터이므로, 레코드가 있는데도 status가
    pending/checked_missing 으로 남아 있는 경우를 정합성 있게 교정한다.

한 번 실행용(one-shot) backfill 커맨드이므로 멱등성이 보장된다.
레코드가 이미 'confirmed'인 경우 카운터에만 집계하고 업데이트는 건너뛴다.

사용:
    python manage.py backfill_status
    python manage.py backfill_status --dry-run
    python manage.py backfill_status --batch-size 500
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Q

from g2b.models import BidAnnouncement, BidApiAValue, BidApiPrelimPrice
from g2b.services.g2b_construction_sync import PLACEHOLDER_PRELIM_SEQUENCE


class Command(BaseCommand):
    help = 'BidApiAValue/BidApiPrelimPrice 레코드 존재 공고의 status를 confirmed로 backfill합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 DB 변경 없이 대상 건수만 출력',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='한 번에 처리할 공고 수 (기본 1000)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        # A값 레코드가 있는 (공고번호, 차수) 집합
        a_value_pairs = set(
            BidApiAValue.objects.values_list('bid_ntce_no', 'bid_ntce_ord')
        )

        # 기초금액 레코드(placeholder sequence=0)가 있는 (공고번호, 차수) 집합
        base_amount_pairs = set(
            BidApiPrelimPrice.objects.filter(
                sequence_no=PLACEHOLDER_PRELIM_SEQUENCE,
            ).values_list('bid_ntce_no', 'bid_ntce_ord')
        )

        self.stdout.write(
            f'A값 레코드: {len(a_value_pairs):,}건 / '
            f'기초금액 레코드: {len(base_amount_pairs):,}건'
        )

        # status가 confirmed가 아닌 공고만 대상
        # (confirmed이면 이미 정합, 업데이트 불필요)
        candidates = list(
            BidAnnouncement.objects.filter(
                Q(a_value_status__in=['pending', 'checked_missing'])
                | Q(base_amount_status__in=['pending', 'checked_missing'])
            ).values('id', 'bid_ntce_no', 'bid_ntce_ord', 'a_value_status', 'base_amount_status')
        )

        a_to_confirm_ids = []
        base_to_confirm_ids = []

        for row in candidates:
            key = (row['bid_ntce_no'], row['bid_ntce_ord'])

            # A값: 레코드 있으면 confirmed로
            if row['a_value_status'] in ('pending', 'checked_missing') and key in a_value_pairs:
                a_to_confirm_ids.append(row['id'])

            # 기초금액: 레코드 있으면 confirmed로
            if row['base_amount_status'] in ('pending', 'checked_missing') and key in base_amount_pairs:
                base_to_confirm_ids.append(row['id'])

        self.stdout.write(
            f'backfill 대상: A값 {len(a_to_confirm_ids):,}건, '
            f'기초금액 {len(base_to_confirm_ids):,}건'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run: DB 변경 없이 종료합니다.'))
            return

        # 배치 업데이트 — OOM 방지를 위해 chunk 처리
        a_updated = 0
        for i in range(0, len(a_to_confirm_ids), batch_size):
            chunk = a_to_confirm_ids[i:i + batch_size]
            a_updated += BidAnnouncement.objects.filter(pk__in=chunk).update(
                a_value_status='confirmed'
            )

        base_updated = 0
        for i in range(0, len(base_to_confirm_ids), batch_size):
            chunk = base_to_confirm_ids[i:i + batch_size]
            base_updated += BidAnnouncement.objects.filter(pk__in=chunk).update(
                base_amount_status='confirmed'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'backfill 완료: A값 {a_updated:,}건, 기초금액 {base_updated:,}건 → confirmed'
            )
        )
