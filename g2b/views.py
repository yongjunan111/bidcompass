"""BC-39/40: 가격점수 계산기 + 최적투찰 추천기 + 벤치마크 뷰."""

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.shortcuts import render

from g2b.services.bid_engine import (
    AValueItems,
    BidAnalysisEngine,
    TableType,
    WorkType,
    get_floor_rate,
    select_table,
)
from g2b.services.optimal_bid import (
    TABLE_PARAMS_MAP,
    OptimalBidInput,
    _score_fast,
    compute_expected_score,
    find_optimal_bid,
    generate_scenarios,
)

_HEATMAP_MAX_SCORES = frozenset({Decimal("90"), Decimal("80"), Decimal("70"), Decimal("50")})


def index(request):
    return render(request, 'g2b/index.html')


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

def _get_prelim_values(post_data=None):
    """POST 데이터에서 prelim_0~14 값을 리스트로 추출 (폼 유지용)."""
    values = []
    for i in range(15):
        if post_data:
            values.append(post_data.get(f'prelim_{i}', ''))
        else:
            values.append('')
    return values


def recommend(request):
    context = {'prelim_values': _get_prelim_values()}
    if request.method == 'POST':
        context['prelim_values'] = _get_prelim_values(request.POST)
        estimated_price = _parse_int(request.POST.get('estimated_price'))
        work_type_str = request.POST.get('work_type', 'construction')
        a_value = _parse_int(request.POST.get('a_value'))
        net_cost = _parse_int(request.POST.get('net_construction_cost')) or None

        if estimated_price <= 0:
            context['error'] = '추정가격을 입력하세요.'
            context['form'] = request.POST
            return render(request, 'g2b/recommend.html', context)

        # 복수예비가격 파싱 (최대 15개)
        prelim_prices = []
        for i in range(15):
            val = _parse_int(request.POST.get(f'prelim_{i}'))
            if val > 0:
                prelim_prices.append(val)

        if len(prelim_prices) < 4:
            context['error'] = f'복수예비가격을 최소 4개 입력하세요 (현재 {len(prelim_prices)}개).'
            context['form'] = request.POST
            return render(request, 'g2b/recommend.html', context)

        work_type = (WorkType.SPECIALTY if work_type_str == 'specialty'
                     else WorkType.CONSTRUCTION)

        table_type = select_table(estimated_price, work_type)
        if table_type == TableType.OUT_OF_SCOPE:
            context['error'] = '추정가격 100억 이상은 적격심사 대상 외입니다.'
            context['form'] = request.POST
            return render(request, 'g2b/recommend.html', context)

        try:
            inp = OptimalBidInput(
                preliminary_prices=prelim_prices,
                a_value=a_value,
                table_type=table_type,
                presume_price=estimated_price,
                net_construction_cost=net_cost,
            )
            result = find_optimal_bid(inp)
        except ValueError as e:
            context['error'] = str(e)
            context['form'] = request.POST
            return render(request, 'g2b/recommend.html', context)

        # 밴드 산출: optimal_bid ±100,000 범위에서 step=1,000
        params = TABLE_PARAMS_MAP[table_type]
        max_s = float(params.max_score)
        coeff = float(params.coeff)
        fixed_ratio = float(params.fixed_ratio)
        fixed_score = float(params.fixed_score)

        scenarios = generate_scenarios(prelim_prices)
        optimal_bid = result.recommended_bid
        optimal_score = result.expected_score

        threshold = optimal_score - 0.05

        band_bids = []
        for offset in range(-100, 101):
            test_bid = optimal_bid + offset * 1_000
            if test_bid <= 0:
                continue
            es = compute_expected_score(
                test_bid, scenarios, a_value,
                max_s, coeff, fixed_ratio, fixed_score,
            )
            if es >= threshold:
                band_bids.append(test_bid)

        band_low = min(band_bids) if band_bids else optimal_bid
        band_high = max(band_bids) if band_bids else optimal_bid

        # 시나리오별 점수 분포 (고유 예정가격별)
        scenario_counts = Counter(scenarios)
        unique_scenarios = sorted(scenario_counts)
        scenario_rows = []
        for est in unique_scenarios:
            score = _score_fast(
                optimal_bid, est, a_value,
                max_s, coeff, fixed_ratio, fixed_score,
            )
            count = scenario_counts[est]
            scenario_rows.append({
                'est_price': f"{est:,}",
                'score': f"{score:.2f}",
                'count': count,
                'prob': f"{count / len(scenarios) * 100:.1f}",
            })

        table_label = {
            TableType.TABLE_1: '별표 1',
            TableType.TABLE_2A: '별표 2-가',
            TableType.TABLE_2B: '별표 2-나',
            TableType.TABLE_3: '별표 3',
            TableType.TABLE_4: '별표 4',
            TableType.TABLE_5: '별표 5',
        }

        context['result'] = result
        context['table_label'] = table_label.get(table_type, '')
        context['band_low'] = band_low
        context['band_high'] = band_high
        context['band_low_fmt'] = f"{band_low:,}"
        context['band_high_fmt'] = f"{band_high:,}"
        context['optimal_bid_fmt'] = f"{optimal_bid:,}"
        context['expected_score'] = f"{result.expected_score:.2f}"
        context['min_score'] = f"{result.min_scenario_score:.2f}"
        context['max_score'] = f"{result.max_scenario_score:.2f}"
        context['n_scenarios'] = result.n_scenarios
        context['n_unique_scenarios'] = len(unique_scenarios)
        context['scenario_rows'] = scenario_rows
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
