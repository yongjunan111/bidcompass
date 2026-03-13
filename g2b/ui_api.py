from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db.models import Exists, OuterRef, Q
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from g2b.models import (
    BidAnnouncement,
    BidApiAValue,
    BidApiCollectionLog,
    BidApiPrelimPrice,
    BidContract,
)
from g2b.services.ai_report import ReportInput, generate_report
from g2b.services.bid_engine import (
    ExclusionStatus,
    TableType,
    WorkType,
    calc_price_score,
    check_net_cost_exclusion,
    get_floor_rate,
    select_table,
)
from g2b.services.prebid_recommend import prebid_recommend
from g2b.services.report_stats import get_similar_bid_stats


@dataclass
class NoticeBundle:
    announcement: BidAnnouncement
    contract: BidContract | None
    a_value_total: int
    base_amount: int
    estimated_price: int


SUPPORTED_PRESUME_PRICE_LIMIT = 10_000_000_000


@ensure_csrf_cookie
def frontend_app(request):
    return render(request, 'frontend/app.html')


def _parse_int(value: Any, default: int = 0) -> int:
    if value in (None, ''):
        return default
    try:
        return int(str(value).replace(',', '').strip())
    except (TypeError, ValueError):
        return default


def _parse_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    if value in (None, ''):
        return default
    try:
        return Decimal(str(value).replace(',', '').strip())
    except (InvalidOperation, ValueError, TypeError):
        return default


def _format_currency(amount: int | None) -> str:
    if amount is None:
        return '-'
    return f'₩ {amount:,}'


def _format_plain_currency(amount: int | None) -> str:
    if amount is None:
        return '-'
    return f'{amount:,}원'


def _format_percent(value: float | Decimal | None, digits: int = 3) -> str:
    if value is None:
        return '-'
    return f'{float(value):.{digits}f}%'


def _format_compact_date(value: str | None) -> str:
    if not value:
        return '-'
    digits = ''.join(ch for ch in value if ch.isdigit())
    if len(digits) == 8:
        return f'{digits[0:4]}.{digits[4:6]}.{digits[6:8]}'
    return value


def _format_datetime(value) -> str:
    if not value:
        return '-'
    try:
        return timezone.localtime(value).strftime('%Y.%m.%d %H:%M')
    except Exception:
        return str(value)


def _first_text(*values: str) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return '-'


def _infer_work_type(announcement: BidAnnouncement | None, requested: str | None = None) -> WorkType:
    if requested == 'specialty':
        return WorkType.SPECIALTY
    if requested == 'construction':
        return WorkType.CONSTRUCTION
    if not announcement:
        return WorkType.CONSTRUCTION

    text = ' '.join(
        filter(
            None,
            [
                announcement.license_limit_list,
                announcement.bid_ntce_nm,
            ],
        )
    )
    specialty_keywords = ('전기', '통신', '소방', '국가유산', '문화재', '전문공사')
    if any(keyword in text for keyword in specialty_keywords):
        return WorkType.SPECIALTY
    return WorkType.CONSTRUCTION


def _variance_label(similar_stats: dict) -> str:
    width = float(similar_stats.get('p90_rate', 0) or 0) - float(similar_stats.get('p10_rate', 0) or 0)
    if width <= 0.08:
        return '낮음'
    if width <= 0.18:
        return '보통'
    return '높음'


def _competition_label(similar_stats: dict) -> str:
    bidder_cnt = float(similar_stats.get('avg_bidder_cnt', 0) or 0)
    if bidder_cnt < 20:
        return '낮음'
    if bidder_cnt < 50:
        return '보통'
    return '높음'


def _eligible_contract_queryset():
    return (
        BidContract.objects.filter(
            procurement_type='공사',
            win_method__icontains='적격',
            presume_price__gt=0,
            presume_price__lt=SUPPORTED_PRESUME_PRICE_LIMIT,
        )
        .exclude(bid_ntce_nm='')
    )


def _apply_notice_search_filters(contract_qs, query: str = '', region: str = ''):
    if query:
        contract_qs = contract_qs.filter(
            Q(bid_ntce_no__icontains=query)
            | Q(bid_ntce_nm__icontains=query)
            | Q(license_limit_list__icontains=query)
            | Q(restrict_area_list__icontains=query)
            | Q(demand_org__icontains=query)
            | Q(ntce_org__icontains=query)
        )

    if region:
        contract_qs = contract_qs.filter(
            Q(demand_org_area__icontains=region)
            | Q(restrict_area_list__icontains=region)
            | Q(demand_org__icontains=region)
            | Q(ntce_org__icontains=region)
            | Q(bid_ntce_nm__icontains=region)
        )

    return contract_qs


def _eligible_announcement_queryset():
    eligible_contracts = _eligible_contract_queryset().filter(
        bid_ntce_no=OuterRef('bid_ntce_no'),
        bid_ntce_ord=OuterRef('bid_ntce_ord'),
    )
    return (
        BidAnnouncement.objects.exclude(bid_ntce_nm='')
        .annotate(has_eligible_contract=Exists(eligible_contracts))
        .filter(has_eligible_contract=True)
    )


def _eligible_collection_log_queryset():
    eligible_contracts = _eligible_contract_queryset().filter(
        bid_ntce_no=OuterRef('bid_ntce_no'),
        bid_ntce_ord=OuterRef('bid_ntce_ord'),
    )
    return (
        BidApiCollectionLog.objects.annotate(
            has_eligible_contract=Exists(eligible_contracts)
        )
        .filter(has_eligible_contract=True)
    )


def _is_supported_bundle(bundle: NoticeBundle) -> bool:
    contract = bundle.contract
    if not contract:
        return False
    if contract.procurement_type != '공사':
        return False
    if '적격' not in (contract.win_method or ''):
        return False
    if bundle.estimated_price <= 0 or bundle.estimated_price >= SUPPORTED_PRESUME_PRICE_LIMIT:
        return False
    table_type = select_table(bundle.estimated_price, _infer_work_type(bundle.announcement))
    return table_type != TableType.OUT_OF_SCOPE


def _ensure_supported_bundle(bundle: NoticeBundle) -> NoticeBundle:
    if not _is_supported_bundle(bundle):
        raise Http404('건설공사 적격심사 대상 공고만 지원합니다.')
    return bundle


def _lookup_notice_bundle(bid_ntce_no: str, bid_ntce_ord: str | None = None) -> NoticeBundle:
    announcement = (
        BidAnnouncement.objects.filter(
            bid_ntce_no=bid_ntce_no,
            **({'bid_ntce_ord': bid_ntce_ord} if bid_ntce_ord else {}),
        )
        .order_by('-bid_ntce_ord')
        .first()
    )
    if not announcement:
        raise Http404(f'공고번호 {bid_ntce_no}을 찾을 수 없습니다.')

    contract = (
        BidContract.objects.filter(
            bid_ntce_no=announcement.bid_ntce_no,
            bid_ntce_ord=announcement.bid_ntce_ord,
        )
        .order_by('-created_at')
        .first()
    )
    a_value = BidApiAValue.objects.filter(
        bid_ntce_no=announcement.bid_ntce_no,
        bid_ntce_ord=announcement.bid_ntce_ord,
    ).first()
    prelim = BidApiPrelimPrice.objects.filter(
        bid_ntce_no=announcement.bid_ntce_no,
        bid_ntce_ord=announcement.bid_ntce_ord,
    ).first()

    a_value_total = 0
    if a_value:
        a_value_total = (
            a_value.national_pension
            + a_value.health_insurance
            + a_value.retirement_mutual_aid
            + a_value.long_term_care
            + a_value.occupational_safety
            + a_value.safety_management
            + a_value.quality_management
        )

    estimated_price = announcement.presume_price or (contract.presume_price if contract else 0) or 0
    base_amount = prelim.base_amount if prelim and prelim.base_amount else estimated_price

    return NoticeBundle(
        announcement=announcement,
        contract=contract,
        a_value_total=a_value_total,
        base_amount=base_amount,
        estimated_price=estimated_price,
    )


def _serialize_notice_summary(bundle: NoticeBundle) -> dict[str, str]:
    announcement = bundle.announcement
    contract = bundle.contract
    return {
        'id': announcement.bid_ntce_no,
        'title': _first_text(announcement.bid_ntce_nm, '공고명 없음'),
        'agency': _first_text(
            contract.demand_org if contract else '',
            contract.ntce_org if contract else '',
            announcement.ntce_dept,
            announcement.ntce_person,
            '기관 정보 없음',
        ),
        'deadline': _format_compact_date(contract.openg_date if contract else ''),
        'estimate': _format_currency(bundle.estimated_price),
        'sector': _first_text(
            (contract.license_limit_list if contract else '').split(',')[0],
            announcement.license_limit_list.split(',')[0],
            '일반',
        ),
        'region': _first_text(
            contract.demand_org_area if contract else '',
            announcement.site_area,
            announcement.restrict_area_list.split(',')[0],
            '전국',
        ),
    }


def _strategy_cards(result, bundle: NoticeBundle, similar_stats: dict) -> list[dict[str, Any]]:
    def bid_rate(amount: int) -> str:
        denominator = bundle.base_amount - bundle.a_value_total
        if denominator <= 0:
            return '-'
        rate = (amount - bundle.a_value_total) / denominator * 100
        return f'{rate:.3f}%'

    variance = _variance_label(similar_stats)
    competition = _competition_label(similar_stats)

    return [
        {
            'key': 'safe',
            'label': '안정형 Safe',
            'rate': bid_rate(result.safe_bid),
            'risk': '매우 낮음',
            'desc': '하한율 여유를 우선 확보하는 보수적 전략입니다.',
            'reason': '하한율 미달 위험을 가장 낮게 유지할 수 있습니다.',
            'expectedRange': '보수 구간',
            'summary': [
                '하한율 방어를 먼저 보는 상황에서 가장 안정적인 안입니다.',
                f'유사 공고 분산은 {variance}이며, 보수적 전략의 설명력이 충분합니다.',
                '첫 보고안이나 내부 검토 초안으로 사용하기 좋습니다.',
            ],
            'amount': _format_currency(result.safe_bid),
        },
        {
            'key': 'base',
            'label': '균형형 Base',
            'rate': bid_rate(result.optimal_bid),
            'risk': '낮음',
            'desc': '안정성과 기대값의 균형이 가장 좋은 기본 전략입니다.',
            'reason': '가격점수 구조와 유사 공고 분포를 함께 반영한 기본안입니다.',
            'expectedRange': '중앙값 인접',
            'summary': [
                '기본 추천안으로 설명하기 가장 쉬운 카드입니다.',
                f'최근 경쟁 강도는 {competition}이며, 과도한 공격 전략은 필요하지 않습니다.',
                '실무자가 기본안과 비교안을 함께 보고 판단하기에 적합합니다.',
            ],
            'amount': _format_currency(result.optimal_bid),
        },
        {
            'key': 'aggressive',
            'label': '적극형 Aggressive',
            'rate': bid_rate(result.aggressive_bid),
            'risk': '보통',
            'desc': '상대적으로 높은 기대값을 검토하는 비교 전략입니다.',
            'reason': '기본안보다 공격적인 선택지를 비교하기 위한 카드입니다.',
            'expectedRange': '상단 구간',
            'summary': [
                '기대값을 더 높게 보고 싶을 때 비교안으로 활용할 수 있습니다.',
                '다만 변동성까지 같이 커지므로 기본안보다 설명력이 떨어질 수 있습니다.',
                '최종 제출 전에는 하한율과 내부 허용 리스크를 다시 확인해야 합니다.',
            ],
            'amount': _format_currency(result.aggressive_bid),
        },
    ]


def _build_recommendation_payload(bundle: NoticeBundle) -> dict[str, Any]:
    if bundle.estimated_price <= 0:
        raise Http404('추정가격이 없는 공고는 추천 결과를 계산할 수 없습니다.')

    work_type = _infer_work_type(bundle.announcement)
    table_type = select_table(bundle.estimated_price, work_type)
    if table_type == TableType.OUT_OF_SCOPE:
        raise Http404('적격심사 대상 외 공고입니다.')

    recommendation = prebid_recommend(
        base_amount=bundle.base_amount,
        a_value=bundle.a_value_total,
        table_type=table_type,
        presume_price=bundle.estimated_price,
    )
    similar_stats = get_similar_bid_stats(bundle.estimated_price)
    strategies = _strategy_cards(recommendation, bundle, similar_stats)
    base_strategy = next(item for item in strategies if item['key'] == 'base')

    return {
        'notice': {
            **_serialize_notice_summary(bundle),
            'noticeNo': bundle.announcement.bid_ntce_no,
        },
        'strategies': strategies,
        'judgement': {
            'baseAmount': _format_currency(bundle.base_amount),
            'aValue': _format_currency(bundle.a_value_total),
            'priceScore': f'{recommendation.optimal_score:.2f}',
            'passResult': '통과 PASS' if recommendation.floor_rate_pass else '미달 FAIL',
            'selectedRate': base_strategy['rate'],
        },
        'similar': {
            'count': f"{similar_stats.get('count', 0):,}건",
            'median': _format_percent(similar_stats.get('p50_rate', 0), 3),
            'variance': _variance_label(similar_stats),
            'competition': _competition_label(similar_stats),
        },
        'status': {
            'analysisStatus': '완료',
            'updatedAt': _format_datetime(bundle.announcement.created_at),
            'reportVersion': '',
        },
        'floorRate': _format_percent(recommendation.floor_rate, 3),
        'floorBid': _format_currency(recommendation.floor_rate_bid),
        'band': {
            'low': _format_currency(recommendation.band_low),
            'high': _format_currency(recommendation.band_high),
            'halfWidth': f'±{recommendation.band_half_width:.2f}%p',
        },
        'tableLabel': recommendation.table_label,
        'estimatedPrice': bundle.estimated_price,
        'aValueTotal': bundle.a_value_total,
        'baseAmountValue': bundle.base_amount,
        'floorRateBidValue': recommendation.floor_rate_bid,
    }


def _build_report_blocks(report) -> list[dict[str, Any]]:
    return [
        {
            'title': '핵심 판단',
            'body': report.summary,
            'bullets': report.evidence or ['근거 데이터가 충분하지 않습니다.'],
        },
        {
            'title': '추천 전략',
            'body': report.strategy,
            'bullets': report.action_items or ['실행 항목이 없습니다.'],
        },
        {
            'title': '리스크 포인트',
            'body': '최종 제출 전 확인해야 하는 리스크 항목입니다.',
            'bullets': report.risk_factors or ['확인된 리스크가 없습니다.'],
        },
    ]


@require_GET
def api_dashboard(request):
    today = timezone.localdate().strftime('%Y%m%d')
    display_contracts = _eligible_contract_queryset().filter(openg_date=today).order_by(
        'openg_date', 'bid_ntce_no', 'contract_no'
    )
    notice_rows = []
    seen_notice_numbers: set[str] = set()
    for contract in display_contracts:
        if contract.bid_ntce_no in seen_notice_numbers:
            continue
        seen_notice_numbers.add(contract.bid_ntce_no)
        bundle = _lookup_notice_bundle(contract.bid_ntce_no, contract.bid_ntce_ord)
        notice_rows.append(_serialize_notice_summary(bundle))
        if len(notice_rows) >= 4:
            break

    eligible_logs = _eligible_collection_log_queryset()
    collection_total = eligible_logs.count()
    collection_ok = eligible_logs.filter(
        a_value_status='ok',
        prelim_status='ok',
    ).count()
    collection_error = eligible_logs.filter(
        Q(a_value_status='error') | Q(prelim_status='error')
    ).count()
    completion_rate = (collection_ok / collection_total * 100) if collection_total else 0
    today_visible_total = display_contracts.values('bid_ntce_no').distinct().count()
    eligible_notice_total = _eligible_contract_queryset().values('bid_ntce_no').distinct().count()

    response = {
        'metrics': [
            {'label': '오늘 개찰 건설공고', 'value': f'{today_visible_total:,}건', 'tone': 'accent', 'helper': f'화면 표시 {len(notice_rows)}건'},
            {'label': '추천 가능 공고', 'value': f'{collection_ok:,}건', 'helper': '건설공사 적격심사 기준'},
            {'label': '분석 준비율', 'value': f'{completion_rate:.1f}%', 'tone': 'success', 'helper': '수집 로그 기준'},
            {'label': '건설 적격 공고', 'value': f'{eligible_notice_total:,}건', 'helper': '100억 미만 기준'},
        ],
        'todayNotices': notice_rows,
        'checklist': [
            {'label': '오늘 개찰 건설공고', 'value': f'{today_visible_total:,}건'},
            {'label': '화면 표시 공고', 'value': f'{len(notice_rows):,}건'},
            {'label': '수집 오류 건수', 'value': f'{collection_error:,}건'},
        ],
        'memos': [],
        'weeklyStats': [],
    }
    return JsonResponse(response)


@require_GET
def api_notice_search(request):
    query = request.GET.get('query', '').strip()
    region = request.GET.get('region', '').strip()
    contract_qs = _apply_notice_search_filters(
        _eligible_contract_queryset().order_by('-created_at'),
        query=query,
        region=region,
    )

    seen = set()
    results = []
    for contract in contract_qs[:24]:
        notice_key = (contract.bid_ntce_no, contract.bid_ntce_ord)
        if notice_key in seen:
            continue
        seen.add(notice_key)
        try:
            bundle = _lookup_notice_bundle(contract.bid_ntce_no, contract.bid_ntce_ord)
        except Http404:
            continue
        results.append(_serialize_notice_summary(bundle))
        if len(results) >= 12:
            break

    recent = []
    for contract in contract_qs[:3]:
        recent.append({
            'label': contract.bid_ntce_no,
            'value': _format_datetime(contract.created_at),
        })

    response = {
        'query': query,
        'region': region,
        'count': len(results),
        'results': results,
        'recent': recent,
        'sourceStatus': [],
    }
    return JsonResponse(response)


@require_GET
def api_recommendation_result(request):
    bid_ntce_no = request.GET.get('bid_ntce_no', '').strip()
    if not bid_ntce_no:
        latest = _eligible_announcement_queryset().order_by('-created_at').first()
        if not latest:
            return JsonResponse({'error': '추천 가능한 공고가 없습니다.'}, status=404)
        bundle = _lookup_notice_bundle(latest.bid_ntce_no, latest.bid_ntce_ord)
    else:
        bundle = _lookup_notice_bundle(bid_ntce_no)

    _ensure_supported_bundle(bundle)
    return JsonResponse(_build_recommendation_payload(bundle))


@require_POST
def api_price_calculator(request):
    payload = json.loads(request.body.decode('utf-8') or '{}')
    bid_ntce_no = str(payload.get('noticeNo', '')).strip()
    bundle = _lookup_notice_bundle(bid_ntce_no) if bid_ntce_no else None
    if bundle and not _is_supported_bundle(bundle):
        return JsonResponse({'error': '건설공사 적격심사 대상 공고만 지원합니다.'}, status=400)

    estimated_price = _parse_int(payload.get('estimatedPrice')) or (bundle.estimated_price if bundle else 0)
    base_amount = _parse_int(payload.get('baseAmount')) or (bundle.base_amount if bundle else estimated_price)
    a_value = _parse_int(payload.get('aValue')) or (bundle.a_value_total if bundle else 0)
    bid_rate = _parse_decimal(payload.get('bidRate'), Decimal('0'))
    work_type = _infer_work_type(bundle.announcement if bundle else None, str(payload.get('workType', '')).strip() or None)
    net_cost = _parse_int(payload.get('netConstructionCost'))

    if estimated_price <= 0:
        return JsonResponse({'error': '추정가격 또는 공고번호가 필요합니다.'}, status=400)
    if base_amount <= 0:
        base_amount = estimated_price

    table_type = select_table(estimated_price, work_type)
    if table_type == TableType.OUT_OF_SCOPE:
        return JsonResponse({'error': '적격심사 대상 외 공고입니다.'}, status=400)

    denominator = base_amount - a_value
    if denominator <= 0:
        return JsonResponse({'error': 'A값이 기초금액 이상입니다.'}, status=400)

    bid_amount = math.ceil(a_value + float(bid_rate) / 100 * denominator)
    score_result = calc_price_score(
        bid_price=bid_amount,
        estimated_price=base_amount,
        a_value=a_value,
        table_type=table_type,
    )
    floor_rate = get_floor_rate(estimated_price)
    floor_bid = math.ceil(a_value + float(floor_rate) / 100 * denominator)

    final_pass = bid_amount >= floor_bid
    exclusion_message = None
    if net_cost > 0:
        exclusion = check_net_cost_exclusion(net_cost, bid_amount)
        exclusion_message = exclusion.message
        final_pass = final_pass and exclusion.status != ExclusionStatus.EXCLUDED

    response = {
        'form': {
            'noticeNo': bid_ntce_no,
            'baseAmount': str(base_amount),
            'aValue': str(a_value),
            'bidRate': f'{bid_rate:.3f}',
        },
        'status': {
            'tone': 'success' if final_pass else 'warning',
            'label': '통과' if final_pass else '주의',
            'text': exclusion_message or (
                '현재 입력 기준으로 하한율 미달 위험은 낮으며 가격점수는 정상 범위입니다.'
                if final_pass else
                '하한율 또는 순공사원가 기준을 다시 확인해야 합니다.'
            ),
        },
        'result': {
            'plannedPrice': _format_currency(base_amount),
            'bidAmount': _format_currency(bid_amount),
            'priceScore': f'{float(score_result.score):.2f}',
            'finalResult': '통과 PASS' if final_pass else '재검토 필요',
        },
        'checks': [
            {'label': '하한율 기준', 'value': '충족' if bid_amount >= floor_bid else '미달'},
            {'label': '순공사원가 98%', 'value': exclusion_message or '미입력'},
            {'label': '적용 별표', 'value': table_type.value},
            {'label': '추천안 연계', 'value': '연결됨' if bundle else '미연결'},
        ],
    }
    return JsonResponse(response)


@require_GET
def api_ai_report(request):
    bid_ntce_no = request.GET.get('bid_ntce_no', '').strip()
    if not bid_ntce_no:
        latest = _eligible_announcement_queryset().order_by('-created_at').first()
        if not latest:
            return JsonResponse({'error': '리포트를 생성할 공고가 없습니다.'}, status=404)
        bundle = _lookup_notice_bundle(latest.bid_ntce_no, latest.bid_ntce_ord)
        bid_ntce_no = latest.bid_ntce_no
    else:
        bundle = _lookup_notice_bundle(bid_ntce_no)
    _ensure_supported_bundle(bundle)
    recommendation_payload = _build_recommendation_payload(bundle)
    similar_stats = get_similar_bid_stats(bundle.estimated_price)
    table_type = select_table(bundle.estimated_price, _infer_work_type(bundle.announcement))
    recommendation = prebid_recommend(
        base_amount=bundle.base_amount,
        a_value=bundle.a_value_total,
        table_type=table_type,
        presume_price=bundle.estimated_price,
    )
    report = generate_report(
        ReportInput(
            table_name=recommendation.table_label,
            presume_price=bundle.estimated_price,
            a_value=bundle.a_value_total,
            floor_rate=f'{recommendation.floor_rate:.2f}',
            floor_bid=recommendation.floor_rate_bid,
            band_low=recommendation.band_low,
            band_high=recommendation.band_high,
            base_bid=recommendation.optimal_bid,
            safe_bid=recommendation.safe_bid,
            aggressive_bid=recommendation.aggressive_bid,
            similar_stats=similar_stats,
        )
    )

    response = {
        'metrics': [
            {'label': '권장 기본안', 'value': recommendation_payload['strategies'][1]['label'], 'tone': 'accent', 'helper': recommendation_payload['strategies'][1]['rate']},
            {'label': '비교안', 'value': recommendation_payload['strategies'][0]['label'], 'helper': recommendation_payload['strategies'][0]['rate']},
            {'label': '표본', 'value': f"{similar_stats.get('count', 0):,}건", 'helper': '유사 공고 기준'},
            {'label': '설명력', 'value': _variance_label(similar_stats), 'tone': 'success', 'helper': f"경쟁 { _competition_label(similar_stats) }"},
        ],
        'blocks': _build_report_blocks(report),
        'quoteText': report.strategy,
        'evidenceRows': [
            {'label': '유사 공고 중앙값', 'value': _format_percent(similar_stats.get('p50_rate', 0), 3)},
            {'label': '최근 경쟁강도', 'value': _competition_label(similar_stats)},
            {'label': '리스크 수준', 'value': recommendation_payload['strategies'][1]['risk']},
            {'label': '권장 전략', 'value': recommendation_payload['strategies'][1]['label']},
        ],
        'actions': [
            {'label': '공고번호', 'value': bid_ntce_no},
            {'label': '마지막 생성', 'value': _format_datetime(timezone.now())},
        ],
    }
    return JsonResponse(response)


@require_GET
def api_history(request):
    rows = []
    announcements = _eligible_announcement_queryset().order_by('-created_at')[:8]
    for announcement in announcements:
        try:
            bundle = _lookup_notice_bundle(announcement.bid_ntce_no, announcement.bid_ntce_ord)
            payload = _build_recommendation_payload(bundle)
            strategy = next(item for item in payload['strategies'] if item['key'] == 'base')
        except Exception:
            continue

        status = '검토중'
        if bundle.contract and bundle.contract.openg_date:
            today_digits = timezone.localdate().strftime('%Y%m%d')
            status = '완료' if bundle.contract.openg_date < today_digits else '검토중'

        rows.append(
            {
                'id': announcement.bid_ntce_no,
                'noticeNo': announcement.bid_ntce_no,
                'title': _first_text(announcement.bid_ntce_nm, '공고명 없음'),
                'strategy': strategy['label'],
                'bidRate': strategy['rate'],
                'status': status,
                'updatedAt': _format_datetime(announcement.created_at),
            }
        )

    response = {
        'rows': rows,
        'summary': [
            {'label': '표시 건수', 'value': f'{len(rows):,}건'},
            {'label': '완료', 'value': f"{sum(1 for row in rows if row['status'] == '완료'):,}건"},
            {'label': '검토중', 'value': f"{sum(1 for row in rows if row['status'] == '검토중'):,}건"},
        ],
        'notes': [],
    }
    return JsonResponse(response)


@require_GET
def api_settings(request):
    response = {
        'teamDefaults': {
            'defaultStrategy': '',
            'comparisonCount': '',
            'warningLevel': '',
            'decimalDisplay': '',
        },
        'outputs': {
            'defaultFormat': '',
            'mailAlert': '',
            'savePolicy': '',
            'teamScope': '',
        },
        'audit': [],
        'environment': [],
    }
    return JsonResponse(response)
