from django.contrib import admin

from g2b.models import (
    BidAnnouncement, BidApiAValue, BidApiCollectionLog, BidApiPrelimPrice,
    BidContract, BidResult, LoadLog,
)


@admin.register(BidAnnouncement)
class BidAnnouncementAdmin(admin.ModelAdmin):
    list_display = [
        "bid_ntce_no", "bid_ntce_nm", "presume_price",
        "success_lowest_rate", "ntce_status",
    ]
    list_filter = ["ntce_status", "first_ntce_yn"]
    search_fields = ["bid_ntce_no", "bid_ntce_nm"]


@admin.register(BidContract)
class BidContractAdmin(admin.ModelAdmin):
    list_display = [
        "bid_ntce_no", "bid_ntce_nm", "company_nm",
        "presume_price", "contract_amt", "ntce_date",
    ]
    list_filter = ["procurement_type", "win_method"]
    search_fields = ["bid_ntce_no", "bid_ntce_nm", "company_nm", "company_bizno"]


@admin.register(BidResult)
class BidResultAdmin(admin.ModelAdmin):
    list_display = [
        "bid_ntce_no", "company_nm", "company_bizno",
        "bid_rate", "bid_amt", "openg_rank",
    ]
    list_filter = ["bid_progress_ord"]
    search_fields = ["bid_ntce_no", "bid_ntce_nm", "company_nm", "company_bizno"]


@admin.register(LoadLog)
class LoadLogAdmin(admin.ModelAdmin):
    list_display = [
        "file_name", "table_name", "status",
        "total_rows", "loaded_rows", "started_at",
    ]
    list_filter = ["table_name", "status"]


@admin.register(BidApiAValue)
class BidApiAValueAdmin(admin.ModelAdmin):
    list_display = [
        "bid_ntce_no", "bid_ntce_ord", "price_decision_method", "collected_at",
    ]
    search_fields = ["bid_ntce_no"]


@admin.register(BidApiPrelimPrice)
class BidApiPrelimPriceAdmin(admin.ModelAdmin):
    list_display = [
        "bid_ntce_no", "bid_ntce_ord", "sequence_no",
        "basis_planned_price", "is_drawn",
    ]
    search_fields = ["bid_ntce_no"]


@admin.register(BidApiCollectionLog)
class BidApiCollectionLogAdmin(admin.ModelAdmin):
    list_display = [
        "bid_ntce_no", "bid_ntce_ord",
        "a_value_status", "prelim_status", "updated_at",
    ]
    list_filter = ["a_value_status", "prelim_status"]
    search_fields = ["bid_ntce_no"]
