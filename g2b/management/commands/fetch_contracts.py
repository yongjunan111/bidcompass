"""건설공사 계약정보 수집 (Pipeline 2b).

범용 계약 API(getDataSetOpnStdCntrctInfo)에서 계약 데이터를 가져오고,
BidAnnouncement에 존재하는 건설공사 공고만 필터링하여 BidContract에 적재합니다.

사용:
    python manage.py fetch_contracts --days 7
    python manage.py fetch_contracts --days 3 --dry-run
"""

from __future__ import annotations

import json
import time
from datetime import timedelta
from pathlib import Path

import httpx

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from g2b.models import BidAnnouncement, BidContract
from g2b.services.g2b_construction_client import (
    REQUEST_DELAY,
    fetch_construction_contracts,
    fetch_construction_notices_by_no,
)
from g2b.services.g2b_construction_sync import (
    bulk_upsert,
    map_contract_item_to_bid_contract,
    map_notice_to_announcement,
    ntce_key,
)


RAW_CONTRACTS_DIR = Path(__file__).resolve().parents[3] / "data" / "collected" / "api_raw" / "contracts"


class Command(BaseCommand):
    help = '건설공사 계약정보를 범용 API에서 수집하여 BidContract에 적재합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='최근 N일 조회 (기본 7)')
        parser.add_argument('--limit', type=int, default=0, help='최대 수집 건수')
        parser.add_argument('--dry-run', action='store_true', help='DB 적재 없이 검증만')
        parser.add_argument('--max-backfill', type=int, default=200, help='보조 조회 최대 건수 (기본 200)')

    def handle(self, *args, **options):
        days = max(options['days'], 1)
        limit = options['limit'] or None
        dry_run = options['dry_run']
        max_backfill = options['max_backfill']

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

        RAW_CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
        raw_path = RAW_CONTRACTS_DIR / f"contracts_{start_date}_{end_date}.json"
        raw_path.write_text(json.dumps(fetched_items, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(f'  JSON 원본 저장: {raw_path}')

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

        # BC-자가복구: BidAnnouncement에 없는 공고는 보조 조회로 복구 시도
        missing_keys = {
            ntce_key(item) for item in construction_items
            if ntce_key(item) not in existing_keys
        }
        if missing_keys:
            self.stdout.write(
                f'  미수집 공고 {len(missing_keys)}건 보조 조회 시작 (Pipeline 1 누락 자가복구)...'
            )
            MAX_CONSECUTIVE_429 = 3

            # backfill 대상 제한
            backfill_targets = sorted(missing_keys)
            if len(backfill_targets) > max_backfill:
                self.stdout.write(
                    f'  보조 조회 대상 {len(backfill_targets)}건 중 {max_backfill}건만 수행'
                )
                backfill_targets = backfill_targets[:max_backfill]

            backfilled_announcements = []
            consecutive_429 = 0

            for i, (ntce_no, ntce_ord) in enumerate(backfill_targets):
                try:
                    notice_items = fetch_construction_notices_by_no(ntce_no, ntce_ord)
                    consecutive_429 = 0  # 성공 시 리셋
                    if notice_items:
                        for notice_item in notice_items:
                            row = map_notice_to_announcement(notice_item)
                            backfilled_announcements.append(row)
                            existing_keys.add((row['bid_ntce_no'], row['bid_ntce_ord']))
                    else:
                        self.stdout.write(
                            f'    보조 조회 결과 없음: {ntce_no}-{ntce_ord}'
                        )
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        consecutive_429 += 1
                        if consecutive_429 >= MAX_CONSECUTIVE_429:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  429 연속 {MAX_CONSECUTIVE_429}회 — 보조 조회 중단'
                                )
                            )
                            break
                        # backoff: 0.5초 × 2^(n-1)
                        backoff = 0.5 * (2 ** (consecutive_429 - 1))
                        self.stdout.write(f'    429 수신, {backoff:.1f}초 대기 후 재시도 안함 (skip)')
                        time.sleep(backoff)
                    else:
                        consecutive_429 = 0
                        self.stdout.write(
                            f'    보조 조회 실패 (skip): {ntce_no}-{ntce_ord} → {e}'
                        )
                except Exception as e:
                    consecutive_429 = 0
                    self.stdout.write(
                        f'    보조 조회 실패 (skip): {ntce_no}-{ntce_ord} → {e}'
                    )
                finally:
                    time.sleep(REQUEST_DELAY)

                if (i + 1) % 50 == 0:
                    self.stdout.write(f'    보조 조회 진행: {i + 1}/{len(backfill_targets)}')
            if backfilled_announcements and not dry_run:
                with transaction.atomic():
                    bulk_upsert(
                        BidAnnouncement,
                        backfilled_announcements,
                        unique_fields=['bid_ntce_no', 'bid_ntce_ord'],
                    )
                self.stdout.write(
                    f'  보조 공고 upsert: {len(backfilled_announcements)}건'
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
