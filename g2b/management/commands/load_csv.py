import csv
import os
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.utils import timezone

from g2b.models import BidAnnouncement, BidContract, BidResult, LoadLog

# CSV 한글 컬럼명 → 모델 필드명
ANNOUNCEMENT_COLUMNS = {
    "입찰공고번호": "bid_ntce_no",
    "입찰공고차수": "bid_ntce_ord",
    "이전입찰공고번호": "prev_bid_ntce_no",
    "개찰장소명": "openg_plce_nm",
    "입찰공고명": "bid_ntce_nm",
    "최초공고여부": "first_ntce_yn",
    "공고상태": "ntce_status",
    "계약요청접수번호": "cntrct_req_no",
    "계약요청접수차수": "cntrct_req_ord",
    "현장지역": "site_area",
    "발주계획통합번호": "order_plan_no",
    "사전규격등록번호": "pre_spec_reg_no",
    "제한지역목록": "restrict_area_list",
    "면허업종제한목록": "license_limit_list",
    "낙찰방법세부기준번호": "bid_method_no",
    "이용자문서번호": "user_doc_no",
    "물품분류번호목록": "item_class_no_list",
    "세부품명번호목록": "detail_item_list",
    "공고설명회장소명": "explain_plce_nm",
    "연계문서번호값": "link_doc_no",
    "납품기한내용": "delivery_content",
    "영문공고명": "eng_bid_ntce_nm",
    "공고담당자": "ntce_person",
    "공고담당자전화번호": "ntce_person_tel",
    "공고관리부서": "ntce_dept",
    "입찰추정가격": "presume_price",
    "예산금액": "budget_amt",
    "관급금액": "govt_supply_amt",
    "낙찰하한율": "success_lowest_rate",
    "배정예산금액": "assign_budget_amt",
    "총납품기한일수": "total_delivery_days",
    "구매대상합계수량": "purchase_total_qty",
    "구매대상합계금액": "purchase_total_amt",
    "지역의무공동수급비율": "region_joint_ratio",
    "개찰완료건수": "openg_complete_cnt",
    "유찰건수": "fail_cnt",
    "재입찰건수": "rebid_cnt",
    "주업종공사예정금액": "main_work_price",
    "사업금액": "project_amt",
    "입찰공고건수": "bid_ntce_cnt",
    "낙찰자선정건수": "winner_select_cnt",
}

CONTRACT_COLUMNS = {
    "조달방식구분": "procurement_method",
    "조달업무구분": "procurement_type",
    "입찰공고번호": "bid_ntce_no",
    "입찰공고차수": "bid_ntce_ord",
    "공고게시일자": "ntce_date",
    "입찰공고명": "bid_ntce_nm",
    "공고기관": "ntce_org",
    "공고기관코드": "ntce_org_cd",
    "수요기관": "demand_org",
    "수요기관코드": "demand_org_cd",
    "개찰예정일자": "openg_date",
    "입찰방법명": "bid_method",
    "낙찰방법명": "win_method",
    "표준계약방법": "std_contract_method",
    "정보화사업여부": "is_info_biz",
    "면허업종제한목록": "license_limit_list",
    "제한지역코드목록": "restrict_area_list",
    "계약유형명": "contract_type",
    "계약번호": "contract_no",
    "기준일자": "base_date",
    "계약시점대표업체명": "company_nm",
    "업체사업자등록번호": "company_bizno",
    "계약시점여성대표자여부": "woman_ceo_yn",
    "계약시점여성기업인증여부": "woman_cert_yn",
    "계약시점장애인기업인증여부": "disabled_cert_yn",
    "계약시점사회적기업인증여부": "social_cert_yn",
    "계약시점업체대표자명": "ceo_nm",
    "계약시점기업형태구분명": "company_type",
    "계약시점업체법정동명": "company_area",
    "계약요청접수번호": "cntrct_req_no",
    "발주계획통합번호": "order_plan_no",
    "소관구분명": "jurisdiction",
    "수요기관법정동명": "demand_org_area",
    "수요기관사업자등록번호": "demand_org_bizno",
    "입찰추정가격": "presume_price",
    "이용자문서번호": "user_doc_no",
    "계약금액": "contract_amt",
}

BIDRESULT_COLUMNS = {
    "입찰공고번호": "bid_ntce_no",
    "입찰공고차수": "bid_ntce_ord",
    "개찰순위": "openg_rank",
    "대표업체": "company_nm",
    "대표업체사업자등록번호": "company_bizno",
    "입찰분류번호": "bid_class_no",
    "입찰진행차수": "bid_progress_ord",
    "계약요청접수번호": "cntrct_req_no",
    "계약요청접수차수": "cntrct_req_ord",
    "이용자문서번호": "user_doc_no",
    "세부품명번호목록": "detail_item_list",
    "제한지역코드목록": "restrict_area_list",
    "면허업종제한목록": "license_limit_list",
    "물품분류번호목록": "item_class_no_list",
    "영문공고명": "eng_bid_ntce_nm",
    "공사현장목록": "construction_site_list",
    "입찰공고명": "bid_ntce_nm",
    "공공조달분류": "public_procurement_class",
    "투찰율": "bid_rate",
    "낙찰하한율": "success_lowest_rate",
    "기초금액": "base_amt",
    "합계배정금액": "total_assign_amt",
    "배정예산금액": "assign_budget_amt",
    "예정가격": "estimated_price",
    "투찰금액": "bid_amt",
    "입찰참여자수": "bidder_cnt",
    "입찰추정가격": "presume_price",
}

BIGINT_FIELDS = {
    "presume_price", "budget_amt", "govt_supply_amt", "assign_budget_amt",
    "purchase_total_amt", "main_work_price", "project_amt", "contract_amt",
    "base_amt", "total_assign_amt", "estimated_price", "bid_amt",
}
INT_FIELDS = {
    "total_delivery_days", "openg_complete_cnt", "fail_cnt", "rebid_cnt",
    "bid_ntce_cnt", "winner_select_cnt", "bidder_cnt",
}
DECIMAL_FIELDS = {
    "success_lowest_rate", "region_joint_ratio", "bid_rate",
}


BIGINT_MAX = 9223372036854775807


def parse_int(value):
    if not value or not value.strip():
        return None
    try:
        n = int(value.replace(",", ""))
        if abs(n) > BIGINT_MAX:
            return None
        return n
    except (ValueError, TypeError):
        return None


def parse_decimal(value):
    if not value or not value.strip():
        return None
    try:
        return Decimal(value.replace(",", ""))
    except (ValueError, TypeError, InvalidOperation):
        return None


class Command(BaseCommand):
    help = "나라장터 CSV 파일을 DB에 적재합니다"

    def add_arguments(self, parser):
        parser.add_argument("file", help="CSV 파일 경로")
        parser.add_argument(
            "--type",
            choices=["announcement", "contract", "result"],
            help="데이터 유형 (미지정 시 파일명에서 추론)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="배치 크기 (기본: 5000)",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        batch_size = options["batch_size"]

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"파일 없음: {file_path}"))
            return

        data_type = options["type"]
        if not data_type:
            basename = os.path.basename(file_path).lower()
            if "announcement" in basename:
                data_type = "announcement"
            elif "contract" in basename:
                data_type = "contract"
            elif "결과" in os.path.basename(file_path) or "result" in basename:
                data_type = "result"
            else:
                self.stderr.write(self.style.ERROR(
                    "파일 유형을 추론할 수 없습니다. --type을 지정하세요."
                ))
                return

        if data_type == "announcement":
            model = BidAnnouncement
            column_map = ANNOUNCEMENT_COLUMNS
            unique_fields = ["bid_ntce_no", "bid_ntce_ord"]
        elif data_type == "contract":
            model = BidContract
            column_map = CONTRACT_COLUMNS
            unique_fields = ["bid_ntce_no", "bid_ntce_ord", "contract_no"]
        else:
            model = BidResult
            column_map = BIDRESULT_COLUMNS
            unique_fields = [
                "bid_ntce_no", "bid_ntce_ord", "company_bizno",
                "bid_class_no", "bid_progress_ord",
            ]

        file_name = os.path.basename(file_path)
        table_name = model._meta.db_table

        log = LoadLog.objects.create(file_name=file_name, table_name=table_name)
        self.stdout.write(f"적재 시작: {file_name} → {table_name}")

        try:
            header_row_idx, headers = self._find_header(file_path, column_map)
            if header_row_idx is None:
                raise ValueError("CSV에서 헤더 행을 찾을 수 없습니다")

            self.stdout.write(f"  헤더 위치: row {header_row_idx}, 컬럼 수: {len(headers)}")

            # CSV 컬럼 인덱스 → 모델 필드명
            field_indices = {}
            for i, h in enumerate(headers):
                if h in column_map:
                    field_indices[i] = column_map[h]

            # 총 행수 추정 (라인 카운트 기반)
            with open(file_path, encoding="utf-16-le") as f:
                line_count = sum(1 for _ in f)
            total_rows = line_count - header_row_idx - 1  # header 이후 데이터
            log.total_rows = total_rows
            log.save(update_fields=["total_rows"])
            self.stdout.write(f"  데이터 행수 (추정): {total_rows:,}")

            # update 대상 필드 (unique 필드 제외)
            update_fields = [
                f for f in column_map.values() if f not in unique_fields
            ]

            loaded = 0
            skipped = 0
            batch = []

            with open(file_path, encoding="utf-16-le") as f:
                reader = csv.reader(f, delimiter="\t")
                for row_idx, row in enumerate(reader):
                    if row_idx <= header_row_idx:
                        continue

                    kwargs = self._parse_row(row, field_indices)
                    if not kwargs.get("bid_ntce_no"):
                        skipped += 1
                        continue

                    batch.append(model(**kwargs))

                    if len(batch) >= batch_size:
                        model.objects.bulk_create(
                            batch,
                            update_conflicts=True,
                            unique_fields=unique_fields,
                            update_fields=update_fields,
                        )
                        loaded += len(batch)
                        batch = []

                        if loaded % 50000 < batch_size:
                            self.stdout.write(f"  진행: {loaded:,}/{total_rows:,}")

            if batch:
                model.objects.bulk_create(
                    batch,
                    update_conflicts=True,
                    unique_fields=unique_fields,
                    update_fields=update_fields,
                )
                loaded += len(batch)

            log.loaded_rows = loaded
            log.status = "success"
            log.finished_at = timezone.now()
            log.save()

            self.stdout.write(self.style.SUCCESS(
                f"완료: {loaded:,}행 적재, {skipped}행 스킵 ({table_name})"
            ))

        except Exception as e:
            log.status = "error"
            log.error_message = str(e)
            log.finished_at = timezone.now()
            log.save()
            self.stderr.write(self.style.ERROR(f"오류: {e}"))
            raise

    def _find_header(self, file_path, column_map):
        """헤더 행을 자동 탐지 (CSV 컬럼명 매칭)"""
        expected = set(column_map.keys())
        with open(file_path, encoding="utf-16-le") as f:
            reader = csv.reader(f, delimiter="\t")
            for row_idx, row in enumerate(reader):
                row_set = set(c.strip() for c in row)
                if len(expected & row_set) >= len(expected) * 0.8:
                    return row_idx, [c.strip() for c in row]
        return None, None

    def _parse_row(self, row, field_indices):
        """CSV 행을 모델 필드 kwargs로 변환"""
        kwargs = {}
        for col_idx, field_name in field_indices.items():
            if col_idx >= len(row):
                continue
            value = row[col_idx].strip()

            if field_name in BIGINT_FIELDS or field_name in INT_FIELDS:
                kwargs[field_name] = parse_int(value)
            elif field_name in DECIMAL_FIELDS:
                kwargs[field_name] = parse_decimal(value)
            else:
                kwargs[field_name] = value

        return kwargs
