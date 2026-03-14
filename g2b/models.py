from django.db import models


class BidAnnouncement(models.Model):
    """입찰공고 내역 (UI-ADODAA-008R)"""

    # 식별
    bid_ntce_no = models.CharField("입찰공고번호", max_length=40)
    bid_ntce_ord = models.CharField("입찰공고차수", max_length=10)
    prev_bid_ntce_no = models.CharField("이전입찰공고번호", max_length=40, blank=True, default="")

    # 공고 기본정보
    openg_plce_nm = models.CharField("개찰장소명", max_length=200, blank=True, default="")
    bid_ntce_nm = models.TextField("입찰공고명", blank=True, default="")
    first_ntce_yn = models.CharField("최초공고여부", max_length=1, blank=True, default="")
    ntce_status = models.CharField("공고상태", max_length=40, blank=True, default="")
    cntrct_req_no = models.CharField("계약요청접수번호", max_length=40, blank=True, default="")
    cntrct_req_ord = models.CharField("계약요청접수차수", max_length=10, blank=True, default="")
    site_area = models.CharField("현장지역", max_length=200, blank=True, default="")
    order_plan_no = models.CharField("발주계획통합번호", max_length=40, blank=True, default="")
    pre_spec_reg_no = models.CharField("사전규격등록번호", max_length=40, blank=True, default="")

    # 제한/분류
    restrict_area_list = models.TextField("제한지역목록", blank=True, default="")
    license_limit_list = models.TextField("면허업종제한목록", blank=True, default="")
    bid_method_no = models.CharField("낙찰방법세부기준번호", max_length=20, blank=True, default="")
    user_doc_no = models.CharField("이용자문서번호", max_length=200, blank=True, default="")
    item_class_no_list = models.TextField("물품분류번호목록", blank=True, default="")
    detail_item_list = models.TextField("세부품명번호목록", blank=True, default="")

    # 기타 텍스트
    explain_plce_nm = models.CharField("공고설명회장소명", max_length=200, blank=True, default="")
    link_doc_no = models.CharField("연계문서번호값", max_length=200, blank=True, default="")
    delivery_content = models.TextField("납품기한내용", blank=True, default="")
    eng_bid_ntce_nm = models.TextField("영문공고명", blank=True, default="")
    ntce_person = models.CharField("공고담당자", max_length=40, blank=True, default="")
    ntce_person_tel = models.CharField("공고담당자전화번호", max_length=40, blank=True, default="")
    ntce_dept = models.CharField("공고관리부서", max_length=100, blank=True, default="")

    # 금액/비율
    presume_price = models.BigIntegerField("입찰추정가격", null=True, blank=True)
    budget_amt = models.BigIntegerField("예산금액", null=True, blank=True)
    govt_supply_amt = models.BigIntegerField("관급금액", null=True, blank=True)
    success_lowest_rate = models.DecimalField(
        "낙찰하한율", max_digits=10, decimal_places=4, null=True, blank=True
    )
    assign_budget_amt = models.BigIntegerField("배정예산금액", null=True, blank=True)
    total_delivery_days = models.IntegerField("총납품기한일수", null=True, blank=True)
    purchase_total_qty = models.CharField("구매대상합계수량", max_length=40, blank=True, default="")
    purchase_total_amt = models.BigIntegerField("구매대상합계금액", null=True, blank=True)
    region_joint_ratio = models.DecimalField(
        "지역의무공동수급비율", max_digits=10, decimal_places=4, null=True, blank=True
    )

    # 통계
    openg_complete_cnt = models.IntegerField("개찰완료건수", null=True, blank=True)
    fail_cnt = models.IntegerField("유찰건수", null=True, blank=True)
    rebid_cnt = models.IntegerField("재입찰건수", null=True, blank=True)

    # 공사 특화
    main_work_price = models.BigIntegerField("주업종공사예정금액", null=True, blank=True)
    project_amt = models.BigIntegerField("사업금액", null=True, blank=True)
    bid_ntce_cnt = models.IntegerField("입찰공고건수", null=True, blank=True)
    winner_select_cnt = models.IntegerField("낙찰자선정건수", null=True, blank=True)

    STATUS_CHOICES = [
        ('pending', '미조회'),
        ('checked_missing', '조회-없음'),
        ('confirmed', '확인'),
        ('error', '재시도제외'),
    ]

    a_value_status = models.CharField(
        "A값 확정상태", max_length=20, default='pending',
        choices=STATUS_CHOICES,
        help_text='confirmed=공식레코드확인, pending=미확인, checked_missing=조회했으나없음, error=재시도제외',
    )
    base_amount_status = models.CharField(
        "기초금액 확정상태", max_length=20, default='pending',
        choices=STATUS_CHOICES,
        help_text='confirmed=공식레코드확인, pending=미확인, checked_missing=조회했으나없음, error=재시도제외',
    )

    a_value_checked_at = models.DateTimeField('A값 최종조회일시', null=True, blank=True)
    base_amount_checked_at = models.DateTimeField('기초금액 최종조회일시', null=True, blank=True)

    # 추가 공고 정보 (API 미수집 → 신규 매핑)
    briefing_yn = models.CharField("설명회실시여부", max_length=1, blank=True, default="")
    briefing_date = models.CharField("설명회일자", max_length=8, blank=True, default="")
    briefing_time = models.CharField("설명회시각", max_length=4, blank=True, default="")
    industry_limit_yn = models.CharField("업종제한여부", max_length=1, blank=True, default="")
    region_limit_yn = models.CharField("지역제한여부", max_length=1, blank=True, default="")
    reserve_price_method = models.CharField("예정가격결정방법", max_length=40, blank=True, default="")
    bid_ntce_url = models.CharField("공고URL", max_length=500, blank=True, default="")

    created_at = models.DateTimeField("적재일시", auto_now_add=True)

    class Meta:
        unique_together = [("bid_ntce_no", "bid_ntce_ord")]
        verbose_name = "입찰공고"
        verbose_name_plural = "입찰공고"
        indexes = [
            models.Index(fields=["presume_price"]),
            models.Index(fields=["ntce_status"]),
        ]

    def __str__(self):
        return f"[{self.bid_ntce_no}] {self.bid_ntce_nm[:50]}"


class BidContract(models.Model):
    """입찰공고 및 계약내역 (UI-ADOXFA-076R)"""

    # 분류
    procurement_method = models.CharField("조달방식구분", max_length=40, blank=True, default="")
    procurement_type = models.CharField("조달업무구분", max_length=40, blank=True, default="")

    # 공고 식별
    bid_ntce_no = models.CharField("입찰공고번호", max_length=40)
    bid_ntce_ord = models.CharField("입찰공고차수", max_length=10)
    ntce_date = models.CharField("공고게시일자", max_length=10, blank=True, default="")
    bid_ntce_nm = models.TextField("입찰공고명", blank=True, default="")

    # 기관
    ntce_org = models.CharField("공고기관", max_length=200, blank=True, default="")
    ntce_org_cd = models.CharField("공고기관코드", max_length=20, blank=True, default="")
    demand_org = models.CharField("수요기관", max_length=200, blank=True, default="")
    demand_org_cd = models.CharField("수요기관코드", max_length=20, blank=True, default="")

    # 입찰
    openg_date = models.CharField("개찰예정일자", max_length=10, blank=True, default="")
    bid_method = models.CharField("입찰방법명", max_length=40, blank=True, default="")
    win_method = models.CharField("낙찰방법명", max_length=40, blank=True, default="")
    std_contract_method = models.CharField("표준계약방법", max_length=40, blank=True, default="")
    is_info_biz = models.CharField("정보화사업여부", max_length=1, blank=True, default="")
    license_limit_list = models.TextField("면허업종제한목록", blank=True, default="")
    restrict_area_list = models.TextField("제한지역코드목록", blank=True, default="")

    # 계약
    contract_type = models.CharField("계약유형명", max_length=40, blank=True, default="")
    contract_no = models.CharField("계약번호", max_length=40, blank=True, default="")
    base_date = models.CharField("기준일자", max_length=10, blank=True, default="")

    # 업체
    company_nm = models.CharField("계약시점대표업체명", max_length=200, blank=True, default="")
    company_bizno = models.CharField("업체사업자등록번호", max_length=20, blank=True, default="")
    woman_ceo_yn = models.CharField("계약시점여성대표자여부", max_length=1, blank=True, default="")
    woman_cert_yn = models.CharField("계약시점여성기업인증여부", max_length=1, blank=True, default="")
    disabled_cert_yn = models.CharField("계약시점장애인기업인증여부", max_length=1, blank=True, default="")
    social_cert_yn = models.CharField("계약시점사회적기업인증여부", max_length=1, blank=True, default="")
    ceo_nm = models.CharField("계약시점업체대표자명", max_length=40, blank=True, default="")
    company_type = models.CharField("계약시점기업형태구분명", max_length=40, blank=True, default="")
    company_area = models.CharField("계약시점업체법정동명", max_length=100, blank=True, default="")

    # 기타
    cntrct_req_no = models.CharField("계약요청접수번호", max_length=40, blank=True, default="")
    order_plan_no = models.CharField("발주계획통합번호", max_length=40, blank=True, default="")
    jurisdiction = models.CharField("소관구분명", max_length=40, blank=True, default="")
    demand_org_area = models.CharField("수요기관법정동명", max_length=100, blank=True, default="")
    demand_org_bizno = models.CharField("수요기관사업자등록번호", max_length=20, blank=True, default="")

    # 금액
    presume_price = models.BigIntegerField("입찰추정가격", null=True, blank=True)
    user_doc_no = models.CharField("이용자문서번호", max_length=200, blank=True, default="")
    contract_amt = models.BigIntegerField("계약금액", null=True, blank=True)

    created_at = models.DateTimeField("적재일시", auto_now_add=True)

    class Meta:
        unique_together = [("bid_ntce_no", "bid_ntce_ord", "contract_no")]
        verbose_name = "공고계약"
        verbose_name_plural = "공고계약"
        indexes = [
            models.Index(fields=["ntce_date"]),
            models.Index(fields=["presume_price"]),
            models.Index(fields=["company_bizno"]),
        ]

    def __str__(self):
        return f"[{self.bid_ntce_no}] {self.bid_ntce_nm[:50]}"


class BidResult(models.Model):
    """입찰공고 결과내역 (UI-ADOFAA-003R)"""

    # 식별
    bid_ntce_no = models.CharField("입찰공고번호", max_length=40)
    bid_ntce_ord = models.CharField("입찰공고차수", max_length=10)
    openg_rank = models.CharField("개찰순위", max_length=10, blank=True, default="")

    # 업체
    company_nm = models.CharField("대표업체", max_length=100, blank=True, default="")
    company_bizno = models.CharField("대표업체사업자등록번호", max_length=20, blank=True, default="")

    # 입찰 분류/차수
    bid_class_no = models.CharField("입찰분류번호", max_length=10, blank=True, default="")
    bid_progress_ord = models.CharField("입찰진행차수", max_length=10, blank=True, default="")
    cntrct_req_no = models.CharField("계약요청접수번호", max_length=40, blank=True, default="")
    cntrct_req_ord = models.CharField("계약요청접수차수", max_length=10, blank=True, default="")
    user_doc_no = models.CharField("이용자문서번호", max_length=200, blank=True, default="")

    # 분류/제한
    detail_item_list = models.TextField("세부품명번호목록", blank=True, default="")
    restrict_area_list = models.TextField("제한지역코드목록", blank=True, default="")
    license_limit_list = models.TextField("면허업종제한목록", blank=True, default="")
    item_class_no_list = models.TextField("물품분류번호목록", blank=True, default="")
    eng_bid_ntce_nm = models.TextField("영문공고명", blank=True, default="")
    construction_site_list = models.TextField("공사현장목록", blank=True, default="")
    bid_ntce_nm = models.TextField("입찰공고명", blank=True, default="")
    public_procurement_class = models.CharField("공공조달분류", max_length=100, blank=True, default="")

    # 금액/비율
    bid_rate = models.DecimalField(
        "투찰율", max_digits=20, decimal_places=4, null=True, blank=True
    )
    success_lowest_rate = models.DecimalField(
        "낙찰하한율", max_digits=20, decimal_places=4, null=True, blank=True
    )
    base_amt = models.BigIntegerField("기초금액", null=True, blank=True)
    total_assign_amt = models.BigIntegerField("합계배정금액", null=True, blank=True)
    assign_budget_amt = models.BigIntegerField("배정예산금액", null=True, blank=True)
    estimated_price = models.BigIntegerField("예정가격", null=True, blank=True)
    bid_amt = models.BigIntegerField("투찰금액", null=True, blank=True)
    bidder_cnt = models.IntegerField("입찰참여자수", null=True, blank=True)
    presume_price = models.BigIntegerField("입찰추정가격", null=True, blank=True)

    created_at = models.DateTimeField("적재일시", auto_now_add=True)

    class Meta:
        unique_together = [
            ("bid_ntce_no", "bid_ntce_ord", "company_bizno",
             "bid_class_no", "bid_progress_ord")
        ]
        verbose_name = "입찰결과"
        verbose_name_plural = "입찰결과"
        indexes = [
            models.Index(fields=["company_bizno"]),
            models.Index(fields=["presume_price"]),
        ]

    def __str__(self):
        return f"[{self.bid_ntce_no}] {self.company_nm} ({self.bid_rate}%)"


class LoadLog(models.Model):
    """CSV 적재 이력"""

    STATUS_CHOICES = [
        ("running", "진행중"),
        ("success", "성공"),
        ("error", "오류"),
    ]

    file_name = models.CharField("파일명", max_length=200)
    table_name = models.CharField("테이블", max_length=100)
    status = models.CharField("상태", max_length=10, choices=STATUS_CHOICES, default="running")
    total_rows = models.IntegerField("총행수", default=0)
    loaded_rows = models.IntegerField("적재행수", default=0)
    error_message = models.TextField("오류메시지", blank=True, default="")
    started_at = models.DateTimeField("시작시각", auto_now_add=True)
    finished_at = models.DateTimeField("종료시각", null=True, blank=True)

    class Meta:
        verbose_name = "적재이력"
        verbose_name_plural = "적재이력"
        ordering = ["-started_at"]

    def __str__(self):
        return f"[{self.table_name}] {self.file_name} ({self.status})"


class BidApiAValue(models.Model):
    """API 수집: A값 7개 항목 (입찰공고정보서비스)"""

    bid_ntce_no = models.CharField("입찰공고번호", max_length=40)
    bid_ntce_ord = models.CharField("입찰공고차수", max_length=10)

    # 7개 A값 필드 (원 단위)
    national_pension = models.BigIntegerField("국민연금", default=0)
    health_insurance = models.BigIntegerField("건강보험", default=0)
    retirement_mutual_aid = models.BigIntegerField("퇴직공제", default=0)
    long_term_care = models.BigIntegerField("장기요양", default=0)
    occupational_safety = models.BigIntegerField("산업안전", default=0)
    safety_management = models.BigIntegerField("안전관리", default=0)
    quality_management = models.BigIntegerField("품질관리", default=0)

    price_decision_method = models.CharField(
        "예정가격결정방식", max_length=40, blank=True, default=""
    )
    collected_at = models.DateTimeField("수집일시", auto_now_add=True)

    class Meta:
        unique_together = [("bid_ntce_no", "bid_ntce_ord")]
        verbose_name = "API A값"
        verbose_name_plural = "API A값"

    def __str__(self):
        return f"[{self.bid_ntce_no}-{self.bid_ntce_ord}] A값"


class BidApiPrelimPrice(models.Model):
    """API 수집: 복수예비가격 (공고당 최대 15개)"""

    bid_ntce_no = models.CharField("입찰공고번호", max_length=40)
    bid_ntce_ord = models.CharField("입찰공고차수", max_length=10)
    sequence_no = models.IntegerField("순번")

    basis_planned_price = models.BigIntegerField("개별예비가격", default=0)
    is_drawn = models.BooleanField("추첨여부", default=False)
    draw_count = models.IntegerField("선택횟수", default=0)
    planned_price = models.BigIntegerField("예정가격", default=0)
    base_amount = models.BigIntegerField("기초금액", default=0)
    collected_at = models.DateTimeField("수집일시", auto_now_add=True)

    class Meta:
        unique_together = [("bid_ntce_no", "bid_ntce_ord", "sequence_no")]
        verbose_name = "API 복수예비가격"
        verbose_name_plural = "API 복수예비가격"

    def __str__(self):
        return f"[{self.bid_ntce_no}-{self.bid_ntce_ord}] #{self.sequence_no}"


class BidApiCollectionLog(models.Model):
    """API 수집 상태 추적 (공고별, 재시작 가능)"""

    STATUS_CHOICES = [
        ("pending", "대기"),
        ("ok", "성공"),
        ("empty", "비대상"),
        ("error", "오류"),
    ]

    bid_ntce_no = models.CharField("입찰공고번호", max_length=40)
    bid_ntce_ord = models.CharField("입찰공고차수", max_length=10)
    a_value_status = models.CharField(
        "A값 상태", max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    prelim_status = models.CharField(
        "복수예비가격 상태", max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    error_detail = models.TextField("오류 상세", blank=True, default="")
    created_at = models.DateTimeField("생성일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정일시", auto_now=True)

    class Meta:
        unique_together = [("bid_ntce_no", "bid_ntce_ord")]
        verbose_name = "API 수집 로그"
        verbose_name_plural = "API 수집 로그"
        indexes = [
            models.Index(fields=["a_value_status"]),
            models.Index(fields=["prelim_status"]),
        ]

    def __str__(self):
        return (
            f"[{self.bid_ntce_no}-{self.bid_ntce_ord}] "
            f"A={self.a_value_status} P={self.prelim_status}"
        )
