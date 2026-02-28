"""데이터 검증 커맨드.

사용:
    python manage.py verify_data
    python manage.py verify_data --sample 5
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Max, Min

from g2b.models import BidAnnouncement, Contract, FetchLog, SuccessfulBid


class Command(BaseCommand):
    help = "수집된 G2B 데이터를 검증합니다"

    def add_arguments(self, parser):
        parser.add_argument("--sample", type=int, default=0, help="샘플 N건 표시")

    def handle(self, *args, **options):
        sample_n = options["sample"]

        self.stdout.write("=" * 70)
        self.stdout.write("  G2B 데이터 검증 리포트")
        self.stdout.write("=" * 70)

        # 테이블별 건수 및 날짜 범위
        self._report_table(
            "입찰공고", BidAnnouncement, "bid_ntce_dt", sample_n,
            display_fields=["bid_ntce_no", "bid_ntce_nm", "presmpt_prce", "bid_ntce_dt"],
        )
        self._report_table(
            "낙찰정보", SuccessfulBid, "fetched_at", sample_n,
            display_fields=["bid_ntce_no", "prcbdr_nm", "bidprc_amt", "sucsf_yn"],
        )
        self._report_table(
            "계약정보", Contract, "cntrct_cncls_de", sample_n,
            display_fields=["cntrct_no", "cntrct_biz_nm", "cntrct_amt", "cntrct_cncls_de"],
        )

        # 고아 레코드 체크
        self._check_orphans()

        # FetchLog 요약
        self._report_fetch_logs()

        self.stdout.write("=" * 70)

    def _report_table(self, label, model, date_field, sample_n, display_fields):
        count = model.objects.count()
        self.stdout.write(f"\n[{label}] 총 {count:,}건")

        if count > 0:
            agg = model.objects.aggregate(
                date_min=Min(date_field),
                date_max=Max(date_field),
            )
            self.stdout.write(
                f"  날짜 범위: {agg['date_min']} ~ {agg['date_max']}"
            )

            if sample_n > 0:
                self.stdout.write(f"  최근 {sample_n}건 샘플:")
                samples = model.objects.order_by("-fetched_at")[:sample_n]
                for obj in samples:
                    vals = [f"{f}={getattr(obj, f, '')}" for f in display_fields]
                    self.stdout.write(f"    {', '.join(vals)}")

    def _check_orphans(self):
        self.stdout.write("\n[고아 레코드 체크]")

        # 낙찰정보가 있는데 공고가 없는 건
        announcement_nos = set(
            BidAnnouncement.objects.values_list("bid_ntce_no", flat=True)
        )
        winning_nos = set(
            SuccessfulBid.objects.values_list("bid_ntce_no", flat=True).distinct()
        )
        orphan_winning = winning_nos - announcement_nos
        self.stdout.write(
            f"  낙찰정보 중 공고 없음: {len(orphan_winning)}건"
        )

        # 계약정보가 있는데 공고가 없는 건
        contract_nos = set(
            Contract.objects.exclude(bid_ntce_no="")
            .values_list("bid_ntce_no", flat=True)
            .distinct()
        )
        orphan_contract = contract_nos - announcement_nos
        self.stdout.write(
            f"  계약정보 중 공고 없음: {len(orphan_contract)}건"
        )

    def _report_fetch_logs(self):
        self.stdout.write("\n[최근 수집이력 (10건)]")
        logs = FetchLog.objects.order_by("-started_at")[:10]
        if not logs:
            self.stdout.write("  (없음)")
            return

        for log in logs:
            duration = ""
            if log.finished_at and log.started_at:
                delta = log.finished_at - log.started_at
                duration = f" ({delta.total_seconds():.1f}초)"
            self.stdout.write(
                f"  [{log.status:7s}] {log.endpoint:20s} "
                f"{log.date_from}~{log.date_to} "
                f"수집={log.fetched_count} 신규={log.created_count} 갱신={log.updated_count}"
                f"{duration}"
            )
            if log.error_message:
                self.stdout.write(f"           오류: {log.error_message[:100]}")
