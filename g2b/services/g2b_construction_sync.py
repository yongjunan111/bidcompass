from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_PRESUME_PRICE_LIMIT = 10_000_000_000
PLACEHOLDER_CONTRACT_NO = 'NOTICE'
PLACEHOLDER_PRELIM_SEQUENCE = 0


def parse_int(value: Any) -> int | None:
    if value in (None, ''):
        return None
    try:
        return int(str(value).replace(',', '').strip())
    except (TypeError, ValueError):
        return None


def parse_decimal(value: Any) -> Decimal | None:
    if value in (None, ''):
        return None
    try:
        return Decimal(str(value).replace(',', '').strip())
    except (InvalidOperation, TypeError, ValueError):
        return None


def _trunc(value: str, max_len: int) -> str:
    """매핑 시점 truncate. bulk_upsert의 _auto_truncate와 이중 적용되나 멱등."""
    return value[:max_len] if len(value) > max_len else value


def compact_date(value: Any) -> str:
    digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
    return digits[:8]


def compact_datetime(value: Any) -> str:
    digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
    return digits[:12]


def join_texts(*values: Any) -> str:
    seen: list[str] = []
    for value in values:
        text = str(value or '').strip()
        if text and text not in seen:
            seen.append(text)
    return ', '.join(seen)


def build_license_limit_list(item: dict[str, Any]) -> str:
    values = [item.get('mainCnsttyNm')]
    values.extend(item.get(f'subsiCnsttyNm{i}') for i in range(1, 10))
    fallback = item.get('bidprcPsblIndstrytyNm')
    license_limit = join_texts(*values)
    return license_limit or str(fallback or '').strip()


def ntce_key(item: dict[str, Any]) -> tuple[str, str]:
    return (item.get('bidNtceNo', '') or '', item.get('bidNtceOrd', '') or '')


def is_eligible_notice_for_service(item: dict[str, Any]) -> bool:
    presume_price = parse_int(item.get('presmptPrce')) or 0
    win_method = str(item.get('sucsfbidMthdNm') or item.get('bidwinrDcsnMthdNm') or '').strip()
    eligible = (
        presume_price > 0
        and presume_price < SUPPORTED_PRESUME_PRICE_LIMIT
        and '적격' in win_method
    )
    if eligible and '적격심사' not in win_method:
        bid_ntce_no = item.get('bidNtceNo', '')
        logger.warning('비표준 적격심사: %s [%s]', win_method, bid_ntce_no)
    return eligible


def is_upcoming_notice(item: dict[str, Any], now_key: str) -> bool:
    openg_key = compact_datetime(item.get('opengDt'))
    if not openg_key:
        return True
    if len(openg_key) < 12:
        return openg_key >= now_key[: len(openg_key)]
    return openg_key >= now_key


def map_notice_to_announcement(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'bid_ntce_no': item.get('bidNtceNo', '') or '',
        'bid_ntce_ord': item.get('bidNtceOrd', '') or '',
        'prev_bid_ntce_no': item.get('refNtceNo', '') or '',
        'openg_plce_nm': item.get('opengPlce', '') or '',
        'bid_ntce_nm': item.get('bidNtceNm', '') or '',
        'first_ntce_yn': 'N' if str(item.get('reNtceYn', '')).strip() == 'Y' else 'Y',
        'ntce_status': _trunc(item.get('ntceKindNm', '') or item.get('bidNtceSttusNm', '') or '', 40),
        'site_area': item.get('cnstrtsiteRgnNm', '') or '',
        'order_plan_no': _trunc(item.get('orderPlanUntyNo', '') or '', 40),
        'pre_spec_reg_no': _trunc(item.get('bfSpecRgstNo', '') or '', 40),
        'restrict_area_list': join_texts(
            item.get('cnstrtsiteRgnNm'),
            item.get('prtcptPsblRgnNm'),
            item.get('rgnLmtBidLocplcJdgmBssNm'),
        ),
        'license_limit_list': build_license_limit_list(item),
        'bid_method_no': item.get('sucsfbidMthdCd', '') or '',
        'explain_plce_nm': item.get('dcmtgOprtnPlce', '') or '',
        'ntce_person': _trunc(item.get('ntceInsttOfclNm', '') or '', 40),
        'ntce_person_tel': _trunc(item.get('ntceInsttOfclTelNo', '') or '', 40),
        'ntce_dept': item.get('ntceInsttNm', '') or '',
        'presume_price': parse_int(item.get('presmptPrce')),
        'budget_amt': parse_int(item.get('bdgtAmt')),
        'govt_supply_amt': parse_int(item.get('govsplyAmt')),
        'success_lowest_rate': parse_decimal(item.get('sucsfbidLwltRate')),
        'assign_budget_amt': parse_int(item.get('bdgtAmt')),
        'region_joint_ratio': parse_decimal(item.get('rgnDutyJntcontrctRt')),
        'main_work_price': parse_int(item.get('mainCnsttyPresmptPrce'))
        or parse_int(item.get('mainCnsttyCnstwkPrearngAmt')),
        'project_amt': parse_int(item.get('bdgtAmt')),
        'briefing_yn': _trunc(item.get('presnatnOprtnYn', '') or '', 1),
        'briefing_date': _trunc(item.get('presnatnOprtnDate', '') or '', 8),
        'briefing_time': _trunc(item.get('presnatnOprtnTm', '') or '', 4),
        'industry_limit_yn': _trunc(item.get('indstrytyLmtYn', '') or '', 1),
        'region_limit_yn': _trunc(item.get('rgnLmtYn', '') or '', 1),
        'reserve_price_method': _trunc(item.get('rsrvtnPrceDcsnMthdNm', '') or '', 40),
        'bid_ntce_url': _trunc(item.get('bidNtceUrl', '') or '', 500),
    }


def map_notice_to_contract(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'procurement_method': _trunc(item.get('cntrctCnclsMthdNm', '') or '', 40),
        'procurement_type': '공사',
        'bid_ntce_no': item.get('bidNtceNo', '') or '',
        'bid_ntce_ord': item.get('bidNtceOrd', '') or '',
        'ntce_date': compact_date(item.get('bidNtceDt')),
        'bid_ntce_nm': item.get('bidNtceNm', '') or '',
        'ntce_org': item.get('ntceInsttNm', '') or '',
        'ntce_org_cd': item.get('ntceInsttCd', '') or '',
        'demand_org': item.get('dminsttNm', '') or '',
        'demand_org_cd': item.get('dminsttCd', '') or '',
        'openg_date': compact_date(item.get('opengDt')),
        'bid_method': _trunc(item.get('bidMethdNm', '') or '', 40),
        'win_method': _trunc(item.get('sucsfbidMthdNm', '') or item.get('bidwinrDcsnMthdNm', '') or '', 40),
        'std_contract_method': _trunc(item.get('cntrctCnclsMthdNm', '') or '', 40),
        'license_limit_list': build_license_limit_list(item),
        'restrict_area_list': join_texts(
            item.get('cnstrtsiteRgnNm'),
            item.get('prtcptPsblRgnNm'),
            item.get('rgnLmtBidLocplcJdgmBssNm'),
        ),
        'contract_type': _trunc(item.get('cntrctCnclsSttusNm', '') or '', 40),
        'contract_no': PLACEHOLDER_CONTRACT_NO,
        'base_date': compact_date(item.get('rgstDt')),
        'cntrct_req_no': _trunc(item.get('untyNtceNo', '') or '', 40),
        'order_plan_no': _trunc(item.get('orderPlanUntyNo', '') or '', 40),
        'demand_org_area': item.get('cnstrtsiteRgnNm', '') or '',
        'presume_price': parse_int(item.get('presmptPrce')),
    }


def map_successful_bid_to_result(
    item: dict[str, Any],
    notice_item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        'bid_ntce_no': item.get('bidNtceNo', '') or '',
        'bid_ntce_ord': item.get('bidNtceOrd', '') or '',
        'openg_rank': '1',
        'company_nm': item.get('bidwinnrNm', '') or '',
        'company_bizno': item.get('bidwinnrBizno', '') or '',
        'bid_class_no': str(item.get('bidClsfcNo', '') or ''),
        'bid_progress_ord': str(item.get('rbidNo', '') or ''),
        'bid_ntce_nm': item.get('bidNtceNm', '') or '',
        'public_procurement_class': '공사',
        'bid_rate': parse_decimal(item.get('sucsfbidRate')),
        'bid_amt': parse_int(item.get('sucsfbidAmt')),
        'bidder_cnt': parse_int(item.get('prtcptCnum')),
        'presume_price': parse_int(notice_item.get('presmptPrce')) if notice_item else None,
        'success_lowest_rate': parse_decimal(notice_item.get('sucsfbidLwltRate')) if notice_item else None,
    }


def map_a_value_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'bid_ntce_no': item.get('bidNtceNo', '') or '',
        'bid_ntce_ord': item.get('bidNtceOrd', '') or '',
        'national_pension': parse_int(item.get('npnInsrprm')) or 0,
        'health_insurance': parse_int(item.get('mrfnHealthInsrprm')) or 0,
        'retirement_mutual_aid': parse_int(item.get('rtrfundNon')) or 0,
        'long_term_care': parse_int(item.get('odsnLngtrmrcprInsrprm')) or 0,
        'occupational_safety': parse_int(item.get('sftyMngcst')) or 0,
        'safety_management': parse_int(item.get('sftyChckMngcst')) or 0,
        'quality_management': parse_int(item.get('qltyMngcst')) or 0,
        'price_decision_method': _trunc(item.get('prearngPrceDcsnMthdNm', '') or '', 40),
    }


def map_prelim_price_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'bid_ntce_no': item.get('bidNtceNo', '') or '',
        'bid_ntce_ord': item.get('bidNtceOrd', '') or '',
        'sequence_no': parse_int(item.get('compnoRsrvtnPrceSno')) or 0,
        'basis_planned_price': parse_int(item.get('bsisPlnprc')) or 0,
        'is_drawn': str(item.get('drwtYn', '')).strip() == 'Y',
        'draw_count': parse_int(item.get('drwtNum')) or 0,
        'planned_price': parse_int(item.get('plnprc')) or 0,
        'base_amount': parse_int(item.get('bssamt')) or 0,
    }


def map_base_amount_to_placeholder_prelim(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'bid_ntce_no': item.get('bidNtceNo', '') or '',
        'bid_ntce_ord': item.get('bidNtceOrd', '') or '',
        'sequence_no': PLACEHOLDER_PRELIM_SEQUENCE,
        'basis_planned_price': 0,
        'is_drawn': False,
        'draw_count': 0,
        'planned_price': 0,
        'base_amount': parse_int(item.get('bssamt')) or 0,
    }


def resolve_server_filters(no_server_filter: bool, stdout) -> 'dict[str, str] | None':
    """서버사이드 필터를 결정하고 로그를 출력한다."""
    from django.conf import settings
    notice_filter = settings.G2B_SERVER_FILTERS['notice']
    if no_server_filter:
        stdout.write('서버필터: 비활성화 (--no-server-filter)')
        return None
    active = {k: v for k, v in notice_filter.items() if v}
    if active:
        stdout.write(f'서버필터: {active}')
    else:
        stdout.write('서버필터: 없음 (환경변수 미설정)')
    return notice_filter


def _auto_truncate(model, rows: list[dict]) -> list[dict]:
    """모델 CharField max_length에 맞춰 자동 truncate (in-place 변경)."""
    limits = {}
    for field in model._meta.fields:
        if hasattr(field, 'max_length') and field.max_length:
            limits[field.name] = field.max_length
    if not limits:
        return rows
    for row in rows:
        for fname, maxlen in limits.items():
            val = row.get(fname)
            if isinstance(val, str) and len(val) > maxlen:
                row[fname] = val[:maxlen]
    return rows


def bulk_upsert(model, rows: list[dict], *, unique_fields: list[str]) -> tuple[int, int]:
    if not rows:
        return 0, 0

    rows = _auto_truncate(model, rows)

    # Deduplicate within batch by unique_fields
    seen_keys: dict[tuple, int] = {}
    for idx, row in enumerate(rows):
        key = tuple(row.get(field) for field in unique_fields)
        seen_keys[key] = idx  # last wins
    rows = [rows[i] for i in sorted(seen_keys.values())]

    bid_numbers = sorted({row['bid_ntce_no'] for row in rows if row.get('bid_ntce_no')})
    existing_keys = set(
        model.objects.filter(bid_ntce_no__in=bid_numbers).values_list(*unique_fields)
    )
    normalized_keys = [
        tuple(row.get(field) for field in unique_fields)
        for row in rows
    ]
    created_count = sum(1 for key in normalized_keys if key not in existing_keys)
    updated_count = len(rows) - created_count

    update_fields = [
        field.name
        for field in model._meta.fields
        if field.name not in {'id', *unique_fields, 'created_at', 'collected_at'}
    ]
    model.objects.bulk_create(
        [model(**row) for row in rows],
        update_conflicts=True,
        unique_fields=unique_fields,
        update_fields=update_fields,
    )
    return created_count, updated_count


def map_contract_item_to_bid_contract(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'procurement_method': _trunc(item.get('cntrctMthdNm', '') or '', 40),
        'procurement_type': '공사',
        'bid_ntce_no': item.get('bidNtceNo', '') or '',
        'bid_ntce_ord': item.get('bidNtceOrd', '') or '',
        'ntce_date': compact_date(item.get('bidNtceDt')),
        'bid_ntce_nm': item.get('bidNtceNm', '') or '',
        'ntce_org': item.get('cntrctInsttNm', '') or '',
        'ntce_org_cd': item.get('cntrctInsttCd', '') or '',
        'demand_org': item.get('dmndInsttNm', '') or '',
        'demand_org_cd': item.get('dmndInsttCd', '') or '',
        'openg_date': compact_date(item.get('opengDate')),
        'bid_method': _trunc(item.get('bidMethdNm', '') or '', 40),
        'win_method': _trunc(item.get('sucsfbidMthdNm', '') or '', 40),
        'std_contract_method': _trunc(item.get('cntrctCnclsMthdNm', '') or '', 40),
        'contract_type': _trunc(item.get('cntrctCnclsSttusNm', '') or '', 40),
        'contract_no': _trunc(item.get('cntrctNo', '') or '', 40),
        'base_date': compact_date(item.get('cntrctCnclsDate')),
        'company_nm': item.get('rprsntCorpNm', '') or '',
        'company_bizno': item.get('rprsntCorpBizrno', '') or '',
        'demand_org_area': item.get('dminsttRgnNm', '') or '',
        'presume_price': parse_int(item.get('presmptPrce')),
        'contract_amt': parse_int(item.get('cntrctAmt')),
    }
