"""BC-39/40/53: 가격점수 계산기 + 사전투찰 추천기 + 벤치마크 + AI 리포트 뷰."""

import json
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from g2b.models import BidAnnouncement, BidApiAValue, BidApiPrelimPrice

from g2b.services.bid_engine import (
    AValueItems,
    BidAnalysisEngine,
    TableType,
    WorkType,
    get_floor_rate,
    select_table,
)
from g2b.services.prebid_recommend import prebid_recommend
from g2b.services.ai_report import ReportInput, generate_report
from g2b.services.report_stats import get_similar_bid_stats

_HEATMAP_MAX_SCORES = frozenset({Decimal("90"), Decimal("80"), Decimal("70"), Decimal("50")})


def index(request):
    return render(request, 'g2b/index.html')


# ──────────────────────────────────────────────
# 공고번호 조회 API (자동 채움)
# ──────────────────────────────────────────────

def lookup_bid(request):
    """공고번호로 추정가격 + A값 + 복수예비가격 조회 (JSON)."""
    ntce_no = request.GET.get('bid_ntce_no', '').strip()
    if not ntce_no:
        return JsonResponse({'error': '공고번호를 입력하세요.'}, status=400)

    # 공고 조회 (최신 차수)
    ann = (BidAnnouncement.objects
           .filter(bid_ntce_no=ntce_no)
           .order_by('-bid_ntce_ord')
           .first())
    if not ann:
        return JsonResponse({'error': f'공고번호 {ntce_no}을 찾을 수 없습니다.'}, status=404)

    result = {
        'bid_ntce_no': ann.bid_ntce_no,
        'bid_ntce_ord': ann.bid_ntce_ord,
        'bid_ntce_nm': ann.bid_ntce_nm,
        'presume_price': ann.presume_price or 0,
    }

    # Canonical source: record existence (NOT BidAnnouncement.a_value_status)
    # status 필드는 배치 메타데이터이며, 추천 판정에 사용하지 않음
    # A값 조회
    av = BidApiAValue.objects.filter(
        bid_ntce_no=ann.bid_ntce_no,
        bid_ntce_ord=ann.bid_ntce_ord,
    ).first()
    if av:
        result['a_value'] = (
            av.national_pension + av.health_insurance +
            av.retirement_mutual_aid + av.long_term_care +
            av.occupational_safety + av.safety_management +
            av.quality_management
        )
        result['a_value_status'] = 'confirmed'
    else:
        result['a_value'] = None  # 0이 아니라 null — 미확정 신호
        result['a_value_status'] = 'missing'

    # 기초금액 조회 (복수예비가격 테이블에서)
    prelim = (BidApiPrelimPrice.objects
              .filter(bid_ntce_no=ann.bid_ntce_no, bid_ntce_ord=ann.bid_ntce_ord)
              .first())
    if prelim:
        result['base_amount'] = prelim.base_amount
        result['base_amount_status'] = 'confirmed'
    else:
        result['base_amount'] = None  # 0이 아니라 null — 미확정 신호
        result['base_amount_status'] = 'missing'

    result['exact_inputs_ready'] = (
        result['a_value_status'] == 'confirmed'
        and result['base_amount_status'] == 'confirmed'
    )

    return JsonResponse(result)


# ──────────────────────────────────────────────
# BC-39: 가격점수 계산기
# ──────────────────────────────────────────────

def _parse_int(value, default=0):
    """폼 입력값 → int 변환. 콤마 허용, 빈값이면 default."""
    if not value:
        return default
    try:
        return int(str(value).replace(',', ''))
    except (ValueError, TypeError):
        return default


def _format_bid_rate(bid_amount: int, base_amount: int, a_value: int) -> str:
    """추천 금액을 기준으로 투찰률(% ) 문자열을 만든다."""
    denominator = base_amount - a_value
    if denominator <= 0:
        return "-"

    rate = (bid_amount - a_value) / denominator * 100
    return f"{rate:.3f}%"


def calculator(request):
    context = {}
    if request.method == 'POST':
        estimated_price = _parse_int(request.POST.get('estimated_price'))
        work_type_str = request.POST.get('work_type', 'construction')
        bid_price = _parse_int(request.POST.get('bid_price')) or None
        net_cost = _parse_int(request.POST.get('net_construction_cost')) or None

        a_items = AValueItems(
            national_pension=_parse_int(request.POST.get('national_pension')),
            health_insurance=_parse_int(request.POST.get('health_insurance')),
            retirement_mutual_aid=_parse_int(request.POST.get('retirement_mutual_aid')),
            long_term_care=_parse_int(request.POST.get('long_term_care')),
            occupational_safety=_parse_int(request.POST.get('occupational_safety')),
            safety_management=_parse_int(request.POST.get('safety_management')),
            quality_management=_parse_int(request.POST.get('quality_management')),
        )

        if estimated_price <= 0:
            context['error'] = '추정가격을 입력하세요.'
            context['form'] = request.POST
            return render(request, 'g2b/calculator.html', context)

        work_type = (WorkType.SPECIALTY if work_type_str == 'specialty'
                     else WorkType.CONSTRUCTION)

        try:
            engine = BidAnalysisEngine(
                estimated_price=estimated_price,
                work_type=work_type,
                a_value_items=a_items,
                bid_price=bid_price,
                net_construction_cost=net_cost,
            )
            result = engine.analyze()
        except ValueError as e:
            context['error'] = str(e)
            context['form'] = request.POST
            return render(request, 'g2b/calculator.html', context)

        table_label = {
            TableType.TABLE_1: '별표 1 (50~100억)',
            TableType.TABLE_2A: '별표 2-가 (10~50억, 일반)',
            TableType.TABLE_2B: '별표 2-나 (3~50억, 전문)',
            TableType.TABLE_3: '별표 3 (3~10억)',
            TableType.TABLE_4: '별표 4 (2~3억 / 0.8~3억 전문)',
            TableType.TABLE_5: '별표 5 (2억 미만 / 0.8억 미만 전문)',
            TableType.OUT_OF_SCOPE: '적격심사 대상 외 (100억 이상)',
        }

        context['result'] = result
        context['table_label'] = table_label.get(result.table_type, '')
        context['floor_rate'] = (
            str(get_floor_rate(estimated_price))
            if result.table_type != TableType.OUT_OF_SCOPE else '-'
        )

        # 히트맵 데이터를 템플릿에서 쓸 수 있도록 변환
        heatmap_rows = []
        for pt in result.score_heatmap:
            heatmap_rows.append({
                'rate_pct': f"{pt.bid_rate * 100:.2f}",
                'bid_amount': f"{pt.bid_amount:,}",
                'score': f"{pt.price_score:.2f}",
                'is_fixed': pt.is_fixed_score,
                'is_max': pt.price_score in _HEATMAP_MAX_SCORES,
            })
        context['heatmap_rows'] = heatmap_rows

        # 폼값 유지
        context['form'] = request.POST

    return render(request, 'g2b/calculator.html', context)


# ──────────────────────────────────────────────
# BC-40: 최적투찰 추천기
# ──────────────────────────────────────────────

def recommend(request):
    """사전 투찰 추천기 — 복수예비가격 없이 기초금액 기반."""
    context = {}
    if request.method == 'POST':
        estimated_price = _parse_int(request.POST.get('estimated_price'))
        base_amount = _parse_int(request.POST.get('base_amount'))
        work_type_str = request.POST.get('work_type', 'construction')
        a_value = _parse_int(request.POST.get('a_value'))
        net_cost = _parse_int(request.POST.get('net_construction_cost')) or None

        # Legacy 편의: POST hidden field로 status 전달.
        # canonical source는 record existence이나, 레거시 뷰에서는
        # 사용자가 직접 입력한 값(user_input)도 허용함.
        a_value_status = request.POST.get('a_value_status', 'user_input')
        base_amount_status = request.POST.get('base_amount_status', 'user_input')
        exact_inputs_ready = (
            a_value_status in ('confirmed', 'user_input')
            and base_amount_status in ('confirmed', 'user_input')
        )

        if not exact_inputs_ready:
            context['warning'] = 'A값 또는 기초금액이 아직 공개되지 않아 정확한 추천이 불가능합니다.'
            context['exact_inputs_ready'] = False
            context['form'] = request.POST
            return render(request, 'g2b/recommend.html', context)

        if estimated_price <= 0:
            context['error'] = '추정가격을 입력하세요.'
            context['form'] = request.POST
            return render(request, 'g2b/recommend.html', context)

        if base_amount <= 0:
            base_amount = estimated_price

        work_type = (WorkType.SPECIALTY if work_type_str == 'specialty'
                     else WorkType.CONSTRUCTION)

        table_type = select_table(estimated_price, work_type)
        if table_type == TableType.OUT_OF_SCOPE:
            context['error'] = '추정가격 100억 이상은 적격심사 대상 외입니다.'
            context['form'] = request.POST
            return render(request, 'g2b/recommend.html', context)

        try:
            result = prebid_recommend(
                base_amount=base_amount,
                a_value=a_value,
                table_type=table_type,
                presume_price=estimated_price,
                net_construction_cost=net_cost,
            )
        except ValueError as e:
            context['error'] = str(e)
            context['form'] = request.POST
            return render(request, 'g2b/recommend.html', context)

        context['result'] = True
        context['exact_inputs_ready'] = True
        context['table_label'] = result.table_label
        context['optimal_bid_fmt'] = f"{result.optimal_bid:,}"
        context['optimal_score'] = f"{result.optimal_score:.0f}"
        context['safe_bid_fmt'] = f"{result.safe_bid:,}"
        context['aggressive_bid_fmt'] = f"{result.aggressive_bid:,}"
        context['band_low_fmt'] = f"{result.band_low:,}"
        context['band_high_fmt'] = f"{result.band_high:,}"
        context['band_half_width'] = f"{result.band_half_width:.2f}"
        context['floor_rate'] = f"{result.floor_rate:.2f}"
        context['floor_rate_bid'] = result.floor_rate_bid
        context['floor_rate_bid_fmt'] = f"{result.floor_rate_bid:,}"
        context['floor_rate_pass'] = result.floor_rate_pass
        context['estimated_price_fmt'] = f"{estimated_price:,}"
        context['base_amount_fmt'] = f"{base_amount:,}"
        context['a_value_fmt'] = f"{a_value:,}"
        context['safe_rate'] = _format_bid_rate(result.safe_bid, base_amount, a_value)
        context['optimal_rate'] = _format_bid_rate(result.optimal_bid, base_amount, a_value)
        context['aggressive_rate'] = _format_bid_rate(result.aggressive_bid, base_amount, a_value)
        context['form'] = request.POST

    return render(request, 'g2b/recommend.html', context)


# ──────────────────────────────────────────────
# 벤치마크 뷰 (BC-38 결과 표시)
# ──────────────────────────────────────────────

def benchmark(request):
    json_path = Path(settings.BASE_DIR) / 'data' / 'collected' / 'benchmark_info21c.json'
    context = {}

    if not json_path.exists():
        context['error_message'] = (
            '벤치마크 데이터가 없습니다. '
            '먼저 python manage.py benchmark_info21c 를 실행하세요.'
        )
        return render(request, 'g2b/benchmark.html', context)

    try:
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        context['error_message'] = f'JSON 파일 로드 실패: {e}'
        return render(request, 'g2b/benchmark.html', context)

    context['meta'] = data.get('meta', {})
    context['summary'] = data.get('summary', {})
    context['records'] = data.get('records', [])

    return render(request, 'g2b/benchmark.html', context)


# ──────────────────────────────────────────────
# BC-53: AI 전략 리포트
# ──────────────────────────────────────────────

def ai_report(request):
    """AI 전략 리포트 — 사전 추천 결과를 AI가 해설."""
    context = {}
    if request.method != 'POST':
        return render(request, 'g2b/ai_report.html', context)

    estimated_price = _parse_int(request.POST.get('estimated_price'))
    base_amount = _parse_int(request.POST.get('base_amount'))
    work_type_str = request.POST.get('work_type', 'construction')
    a_value = _parse_int(request.POST.get('a_value'))
    net_cost = _parse_int(request.POST.get('net_construction_cost')) or None

    # Legacy 편의: POST hidden field로 status 전달.
    # canonical source는 record existence이나, 레거시 뷰에서는
    # 사용자가 직접 입력한 값(user_input)도 허용함.
    a_value_status = request.POST.get('a_value_status', 'user_input')
    base_amount_status = request.POST.get('base_amount_status', 'user_input')
    exact_inputs_ready = (
        a_value_status in ('confirmed', 'user_input')
        and base_amount_status in ('confirmed', 'user_input')
    )

    if not exact_inputs_ready:
        context['warning'] = 'A값 또는 기초금액이 아직 공개되지 않아 AI 리포트를 생성할 수 없습니다.'
        context['exact_inputs_ready'] = False
        context['form'] = request.POST
        return render(request, 'g2b/ai_report.html', context)

    if estimated_price <= 0:
        context['error'] = '추정가격을 입력하세요.'
        context['form'] = request.POST
        return render(request, 'g2b/ai_report.html', context)

    if base_amount <= 0:
        base_amount = estimated_price

    work_type = (WorkType.SPECIALTY if work_type_str == 'specialty'
                 else WorkType.CONSTRUCTION)

    table_type = select_table(estimated_price, work_type)
    if table_type == TableType.OUT_OF_SCOPE:
        context['error'] = '추정가격 100억 이상은 적격심사 대상 외입니다.'
        context['form'] = request.POST
        return render(request, 'g2b/ai_report.html', context)

    try:
        result = prebid_recommend(
            base_amount=base_amount,
            a_value=a_value,
            table_type=table_type,
            presume_price=estimated_price,
            net_construction_cost=net_cost,
        )
    except ValueError as e:
        context['error'] = str(e)
        context['form'] = request.POST
        return render(request, 'g2b/ai_report.html', context)

    # 유사공고 통계
    similar_stats = get_similar_bid_stats(estimated_price)

    # AI 리포트 생성
    report_input = ReportInput(
        table_name=result.table_label,
        presume_price=estimated_price,
        a_value=a_value,
        floor_rate=f"{result.floor_rate:.2f}",
        floor_bid=result.floor_rate_bid,
        band_low=result.band_low,
        band_high=result.band_high,
        base_bid=result.optimal_bid,
        safe_bid=result.safe_bid,
        aggressive_bid=result.aggressive_bid,
        similar_stats=similar_stats,
    )
    report = generate_report(report_input)

    context['result'] = True
    context['table_label'] = result.table_label
    context['optimal_bid_fmt'] = f"{result.optimal_bid:,}"
    context['optimal_score'] = f"{result.optimal_score:.0f}"
    context['safe_bid_fmt'] = f"{result.safe_bid:,}"
    context['aggressive_bid_fmt'] = f"{result.aggressive_bid:,}"
    context['floor_rate'] = f"{result.floor_rate:.2f}"
    context['floor_rate_bid_fmt'] = f"{result.floor_rate_bid:,}"
    context['floor_rate_pass'] = result.floor_rate_pass
    context['similar_stats'] = similar_stats
    context['report'] = report
    context['form'] = request.POST

    return render(request, 'g2b/ai_report.html', context)
