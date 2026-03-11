"""AI 리포트 평가 프레임워크 v5.

테스트셋 자동 선별 → prebid_recommend + report_stats + generate_report 실행
→ 자동 평가 지표 산출 (수치 보존율, 수치 환각, JSON 준수, 응답시간, 비용).
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from typing import List, Optional

from django.core.management.base import BaseCommand
from django.db import connection

from g2b.services.bid_engine import TableType, WorkType, select_table
from g2b.services.prebid_recommend import prebid_recommend
from g2b.services.report_stats import get_similar_bid_stats
from g2b.services.ai_report import ReportInput, ReportOutput, generate_report


# ── 테스트 케이스 구조 ──

@dataclass
class TestCase:
    bid_ntce_no: str
    bid_ntce_ord: str
    presume_price: int
    a_value: int
    base_amount: int
    table_label: str
    # 실제 낙찰 정보 (비교용)
    actual_bid_rate: float
    actual_bidder_cnt: int
    actual_bid_amt: int
    bid_ntce_nm: str
    category: str  # 테스트 분류 (T1, T2A, ..., A값0, FAIL 등)


@dataclass
class EvalResult:
    case: TestCase
    # 타이밍
    total_ms: float
    recommend_ms: float
    stats_ms: float
    report_ms: float
    # 엔진 결과
    base_bid: int
    safe_bid: int
    aggressive_bid: int
    band_low: int
    band_high: int
    floor_rate: str
    floor_bid: int
    similar_count: int
    # 리포트 원문
    report_summary: str
    report_strategy: str
    report_risk_factors: list
    report_evidence: list
    report_action_items: list
    # 자동 평가
    numeric_fidelity_strict: float  # 엄격 보존율 (금액/하한율)
    numeric_fidelity_semantic: float  # 의미 보존율 (통계)
    numeric_fidelity_total: float  # 전체 보존율
    numeric_hallucination_count: int  # 수치 환각 건수
    json_compliant: bool  # JSON 포맷 준수
    is_fallback: bool  # fallback 여부


# ── 수치 보존율 측정 ──

def _normalize_number(text: str) -> Optional[int]:
    """텍스트에서 숫자를 정규화 (쉼표/원/% 제거 → 정수)."""
    cleaned = re.sub(r'[,원%\s]', '', text)
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def _find_number_in_text(target: int, text: str, tolerance: float = 0.0) -> bool:
    """리포트 텍스트에서 target 숫자가 등장하는지 확인.

    tolerance=0.0: exact match (엄격 보존)
    tolerance>0: 비율 허용 (의미 보존)
    """
    # 1) 정규화된 숫자 직접 매칭
    numbers_in_text = re.findall(r'[\d,]+\.?\d*', text)
    for num_str in numbers_in_text:
        normalized = _normalize_number(num_str)
        if normalized is None:
            continue
        if tolerance == 0.0:
            if normalized == target:
                return True
        else:
            if target != 0 and abs(normalized - target) / abs(target) <= tolerance:
                return True
            elif target == 0 and normalized == 0:
                return True

    # 2) 억 단위 변환 확인 (예: 4.6억 = 460,000,000)
    ek_matches = re.findall(r'([\d.]+)\s*억', text)
    for ek_str in ek_matches:
        try:
            ek_val = int(float(ek_str) * 100_000_000)
            if tolerance == 0.0:
                # 억 변환은 반올림 허용 (1천만 이내)
                if abs(ek_val - target) <= 10_000_000:
                    return True
            else:
                if target != 0 and abs(ek_val - target) / abs(target) <= tolerance:
                    return True
        except ValueError:
            continue

    # 3) 만 단위
    man_matches = re.findall(r'([\d,]+)\s*만', text)
    for man_str in man_matches:
        try:
            man_val = int(float(man_str.replace(',', '')) * 10_000)
            if target != 0 and abs(man_val - target) / abs(target) <= tolerance:
                return True
        except ValueError:
            continue

    return False


def _find_rate_in_text(target: float, text: str, tolerance: float = 0.005) -> bool:
    """리포트에서 비율/퍼센트 값 찾기."""
    # 소수점 포함 숫자 찾기
    numbers = re.findall(r'(\d+\.?\d*)\s*%?', text)
    for num_str in numbers:
        try:
            val = float(num_str)
            if abs(val - target) <= tolerance:
                return True
            # 0.xxxx 형태 vs xx.xx% 형태 둘 다 확인
            if abs(val - target * 100) <= tolerance * 100:
                return True
        except ValueError:
            continue
    return False


def measure_numeric_fidelity(inp: ReportInput, report: ReportOutput) -> dict:
    """수치 보존율 측정.

    필수 필드 (엄격 보존 - exact match):
      금액: base_bid, safe_bid, aggressive_bid, band_low, band_high, floor_bid
      비율: floor_rate

    선택 필드 (의미 보존 - 반올림/요약 허용):
      금액: presume_price, a_value
      통계: count, avg_bidder_cnt, p10_rate, p50_rate, p90_rate
    """
    full_text = ' '.join([
        report.summary or '',
        report.strategy or '',
        ' '.join(report.risk_factors or []),
        ' '.join(report.evidence or []),
        ' '.join(report.action_items or []),
    ])

    # 엄격 보존 필드 (금액 + 하한율)
    strict_fields = {
        'base_bid': (inp.base_bid, 'amount'),
        'safe_bid': (inp.safe_bid, 'amount'),
        'aggressive_bid': (inp.aggressive_bid, 'amount'),
        'band_low': (inp.band_low, 'amount'),
        'band_high': (inp.band_high, 'amount'),
        'floor_bid': (inp.floor_bid, 'amount'),
        'floor_rate': (float(inp.floor_rate), 'rate'),
    }

    # 의미 보존 필드 (통계 + 보조 금액)
    stats = inp.similar_stats or {}
    semantic_fields = {
        'presume_price': (inp.presume_price, 'amount'),
        'a_value': (inp.a_value, 'amount'),
        'count': (stats.get('count', 0), 'int'),
        'avg_bidder_cnt': (stats.get('avg_bidder_cnt', 0), 'float'),
        'p10_rate': (stats.get('p10_rate', 0), 'rate'),
        'p50_rate': (stats.get('p50_rate', 0), 'rate'),
        'p90_rate': (stats.get('p90_rate', 0), 'rate'),
    }

    strict_hits = 0
    strict_total = len(strict_fields)
    strict_detail = {}

    for name, (value, vtype) in strict_fields.items():
        if vtype == 'amount':
            found = _find_number_in_text(int(value), full_text, tolerance=0.0)
        else:  # rate
            found = _find_rate_in_text(float(value), full_text, tolerance=0.01)
        strict_detail[name] = found
        if found:
            strict_hits += 1

    semantic_hits = 0
    semantic_total = len(semantic_fields)
    semantic_detail = {}

    for name, (value, vtype) in semantic_fields.items():
        if value == 0:
            semantic_detail[name] = True  # 0이면 언급 안 해도 OK
            semantic_hits += 1
            continue
        if vtype == 'amount':
            found = _find_number_in_text(int(value), full_text, tolerance=0.05)
        elif vtype == 'rate':
            found = _find_rate_in_text(float(value), full_text, tolerance=0.01)
        else:
            found = _find_number_in_text(int(value), full_text, tolerance=0.1)
        semantic_detail[name] = found
        if found:
            semantic_hits += 1

    return {
        'strict_score': strict_hits / strict_total if strict_total else 1.0,
        'semantic_score': semantic_hits / semantic_total if semantic_total else 1.0,
        'total_score': (strict_hits + semantic_hits) / (strict_total + semantic_total),
        'strict_detail': strict_detail,
        'semantic_detail': semantic_detail,
    }


def measure_numeric_hallucination(inp: ReportInput, report: ReportOutput) -> int:
    """수치 환각 측정: 입력에 없는 금액/비율 수치 출력 건수.

    목록 번호, 일반적 서술 숫자는 제외.
    통계 수치는 허용된 반올림/요약이면 환각에서 제외.
    """
    full_text = ' '.join([
        report.summary or '',
        report.strategy or '',
        ' '.join(report.risk_factors or []),
        ' '.join(report.evidence or []),
        ' '.join(report.action_items or []),
    ])

    # 입력에 있는 모든 숫자 수집
    stats = inp.similar_stats or {}
    known_amounts = {
        inp.base_bid, inp.safe_bid, inp.aggressive_bid,
        inp.band_low, inp.band_high, inp.floor_bid,
        inp.presume_price, inp.a_value,
    }
    known_rates = {
        float(inp.floor_rate),
        stats.get('p10_rate', 0), stats.get('p50_rate', 0), stats.get('p90_rate', 0),
        stats.get('avg_bidder_cnt', 0),
    }
    known_ints = {stats.get('count', 0), stats.get('avg_bidder_cnt', 0)}

    # 리포트에서 "도메인 수치"로 보이는 것만 추출
    hallucination_count = 0

    # 금액 패턴: X원, X억, 쉼표 포함 큰 숫자
    amount_patterns = re.findall(r'([\d,]+)\s*원', full_text)
    for amt_str in amount_patterns:
        val = _normalize_number(amt_str)
        if val is None or val < 1_000_000:  # 100만 미만은 서술 숫자로 간주
            continue
        # 입력 금액과 5% 이내면 OK (반올림 허용)
        is_known = any(
            abs(val - k) / max(k, 1) <= 0.05
            for k in known_amounts if k > 0
        )
        if not is_known:
            hallucination_count += 1

    # 억 단위 금액
    ek_patterns = re.findall(r'([\d.]+)\s*억', full_text)
    for ek_str in ek_patterns:
        try:
            ek_val = int(float(ek_str) * 100_000_000)
        except ValueError:
            continue
        if ek_val < 1_000_000:
            continue
        is_known = any(
            abs(ek_val - k) / max(k, 1) <= 0.10  # 억 변환은 10% 허용
            for k in known_amounts if k > 0
        )
        if not is_known:
            hallucination_count += 1

    # 확률/비율 패턴: X% (도메인 의미 있는 것만)
    pct_patterns = re.findall(r'(\d+\.?\d*)\s*%', full_text)
    for pct_str in pct_patterns:
        try:
            val = float(pct_str)
        except ValueError:
            continue
        # 0~5%, 95~100% 범위의 도메인 비율만 체크
        if val < 5 or val > 100:
            continue
        is_known = any(abs(val - k) <= 0.5 for k in known_rates)
        # 90%는 기준율이므로 항상 허용
        if val == 90.0 or val == 98.0:
            is_known = True
        if not is_known:
            hallucination_count += 1

    return hallucination_count


# ── 테스트 케이스 선별 ──

def select_test_cases() -> List[TestCase]:
    """DB에서 테스트 케이스 자동 선별."""
    cases = []

    with connection.cursor() as c:
        # A값 있는 케이스: TABLE별
        for tbl, low, high, limit in [
            ('T1', 0, 300_000_000, 5),
            ('T2A', 300_000_000, 500_000_000, 5),
            ('T3', 500_000_000, 3_000_000_000, 5),
            ('T4', 3_000_000_000, 5_000_000_000, 3),
            ('T5', 5_000_000_000, 10_000_000_000, 3),
        ]:
            c.execute("""
                WITH a_sum AS (
                    SELECT bid_ntce_no, bid_ntce_ord,
                           national_pension + health_insurance + retirement_mutual_aid +
                           long_term_care + occupational_safety + safety_management +
                           quality_management AS a_value
                    FROM g2b_bidapiavalue
                ),
                base AS (
                    SELECT DISTINCT ON (bid_ntce_no, bid_ntce_ord)
                           bid_ntce_no, bid_ntce_ord, base_amount
                    FROM g2b_bidapiprelimprice
                    WHERE base_amount > 0
                    ORDER BY bid_ntce_no, bid_ntce_ord, sequence_no
                )
                SELECT bc.bid_ntce_no, bc.bid_ntce_ord, bc.presume_price,
                       COALESCE(a.a_value, 0),
                       COALESCE(b.base_amount, bc.presume_price),
                       br.bid_rate, br.bidder_cnt, br.bid_amt,
                       bc.bid_ntce_nm
                FROM g2b_bidcontract bc
                JOIN g2b_bidresult br
                    ON bc.bid_ntce_no = br.bid_ntce_no
                    AND bc.bid_ntce_ord = br.bid_ntce_ord
                LEFT JOIN a_sum a
                    ON bc.bid_ntce_no = a.bid_ntce_no
                    AND bc.bid_ntce_ord = a.bid_ntce_ord
                LEFT JOIN base b
                    ON bc.bid_ntce_no = b.bid_ntce_no
                    AND bc.bid_ntce_ord = b.bid_ntce_ord
                WHERE br.openg_rank = '1'
                  AND bc.presume_price BETWEEN %s AND %s
                  AND br.bid_rate > 0
                  AND a.a_value > 0
                ORDER BY RANDOM()
                LIMIT %s
            """, [low, high - 1, limit])

            for row in c.fetchall():
                cases.append(TestCase(
                    bid_ntce_no=row[0], bid_ntce_ord=row[1],
                    presume_price=row[2], a_value=row[3], base_amount=row[4],
                    table_label=tbl,
                    actual_bid_rate=float(row[5]), actual_bidder_cnt=row[6],
                    actual_bid_amt=row[7], bid_ntce_nm=row[8][:50],
                    category=tbl,
                ))

        # A값=0 케이스 (A값 테이블에 없는 공고)
        c.execute("""
            SELECT bc.bid_ntce_no, bc.bid_ntce_ord, bc.presume_price,
                   0 AS a_value, bc.presume_price AS base_amount,
                   br.bid_rate, br.bidder_cnt, br.bid_amt,
                   bc.bid_ntce_nm,
                   CASE
                       WHEN bc.presume_price < 300000000 THEN 'T1'
                       WHEN bc.presume_price < 500000000 THEN 'T2A'
                       WHEN bc.presume_price < 3000000000 THEN 'T3'
                       ELSE 'T4+'
                   END AS tbl
            FROM g2b_bidcontract bc
            JOIN g2b_bidresult br
                ON bc.bid_ntce_no = br.bid_ntce_no
                AND bc.bid_ntce_ord = br.bid_ntce_ord
            LEFT JOIN g2b_bidapiavalue a
                ON bc.bid_ntce_no = a.bid_ntce_no
                AND bc.bid_ntce_ord = a.bid_ntce_ord
            WHERE br.openg_rank = '1'
              AND bc.presume_price BETWEEN 100000000 AND 3000000000
              AND br.bid_rate > 0
              AND br.bidder_cnt > 10
              AND a.bid_ntce_no IS NULL
              AND bc.openg_date >= '20250601'
            ORDER BY RANDOM()
            LIMIT 3
        """)
        for row in c.fetchall():
            cases.append(TestCase(
                bid_ntce_no=row[0], bid_ntce_ord=row[1],
                presume_price=row[2], a_value=0, base_amount=row[4],
                table_label=row[9],
                actual_bid_rate=float(row[5]), actual_bidder_cnt=row[6],
                actual_bid_amt=row[7], bid_ntce_nm=row[8][:50],
                category='A값0',
            ))

    return cases


# ── 평가 실행 ──

def evaluate_case(tc: TestCase) -> EvalResult:
    """단일 테스트 케이스 평가."""
    table_type = select_table(tc.presume_price, WorkType.CONSTRUCTION)

    # 1) prebid_recommend
    t0 = time.perf_counter()
    result = prebid_recommend(
        base_amount=tc.base_amount,
        a_value=tc.a_value,
        table_type=table_type,
        presume_price=tc.presume_price,
    )
    t1 = time.perf_counter()
    recommend_ms = (t1 - t0) * 1000

    # 2) report_stats
    t2 = time.perf_counter()
    similar_stats = get_similar_bid_stats(tc.presume_price)
    t3 = time.perf_counter()
    stats_ms = (t3 - t2) * 1000

    # 3) generate_report
    report_input = ReportInput(
        table_name=result.table_label,
        presume_price=tc.presume_price,
        a_value=tc.a_value,
        floor_rate=f"{result.floor_rate:.2f}",
        floor_bid=result.floor_rate_bid,
        band_low=result.band_low,
        band_high=result.band_high,
        base_bid=result.optimal_bid,
        safe_bid=result.safe_bid,
        aggressive_bid=result.aggressive_bid,
        similar_stats=similar_stats,
    )
    t4 = time.perf_counter()
    report = generate_report(report_input)
    t5 = time.perf_counter()
    report_ms = (t5 - t4) * 1000
    total_ms = (t5 - t0) * 1000

    # 4) 자동 평가
    fidelity = measure_numeric_fidelity(report_input, report)
    hallucination = measure_numeric_hallucination(report_input, report)

    # JSON 준수: 5개 필드 존재 + 타입 확인
    json_ok = all([
        isinstance(report.summary, str) and len(report.summary) > 0,
        isinstance(report.strategy, str) and len(report.strategy) > 0,
        isinstance(report.risk_factors, list),
        isinstance(report.evidence, list),
        isinstance(report.action_items, list),
    ])

    # fallback 판별
    is_fallback = 'AI 리포트 생성 불가' in (report.risk_factors[0] if report.risk_factors else '')

    return EvalResult(
        case=tc,
        total_ms=round(total_ms, 1),
        recommend_ms=round(recommend_ms, 1),
        stats_ms=round(stats_ms, 1),
        report_ms=round(report_ms, 1),
        base_bid=result.optimal_bid,
        safe_bid=result.safe_bid,
        aggressive_bid=result.aggressive_bid,
        band_low=result.band_low,
        band_high=result.band_high,
        floor_rate=f"{result.floor_rate:.2f}",
        floor_bid=result.floor_rate_bid,
        similar_count=similar_stats.get('count', 0),
        report_summary=report.summary,
        report_strategy=report.strategy,
        report_risk_factors=report.risk_factors,
        report_evidence=report.evidence,
        report_action_items=report.action_items,
        numeric_fidelity_strict=round(fidelity['strict_score'], 4),
        numeric_fidelity_semantic=round(fidelity['semantic_score'], 4),
        numeric_fidelity_total=round(fidelity['total_score'], 4),
        numeric_hallucination_count=hallucination,
        json_compliant=json_ok,
        is_fallback=is_fallback,
    )


class Command(BaseCommand):
    help = 'AI 리포트 평가 프레임워크 v5 실행'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0,
                            help='테스트 케이스 수 제한 (0=전체)')
        parser.add_argument('--json', action='store_true',
                            help='JSON 출력')

    def handle(self, *args, **options):
        self.stdout.write('=== AI 리포트 평가 프레임워크 v5 ===\n')

        # 1) 테스트 케이스 선별
        self.stdout.write('테스트 케이스 선별 중...')
        cases = select_test_cases()
        if options['limit'] > 0:
            cases = cases[:options['limit']]
        self.stdout.write(f'  {len(cases)}건 선별 완료\n')

        by_cat = {}
        for c in cases:
            by_cat.setdefault(c.category, []).append(c)
        for cat, items in sorted(by_cat.items()):
            self.stdout.write(f'  {cat}: {len(items)}건')

        # 2) 평가 실행
        self.stdout.write(f'\n평가 실행 중 ({len(cases)}건)...\n')
        results: List[EvalResult] = []
        for i, tc in enumerate(cases):
            self.stdout.write(
                f'  [{i+1}/{len(cases)}] {tc.category} {tc.bid_ntce_no} '
                f'presume={tc.presume_price:,}... ',
                ending=''
            )
            try:
                er = evaluate_case(tc)
                results.append(er)
                status = 'FALLBACK' if er.is_fallback else 'OK'
                self.stdout.write(
                    f'{status} {er.total_ms:.0f}ms '
                    f'fidelity={er.numeric_fidelity_total:.2f} '
                    f'halluc={er.numeric_hallucination_count}'
                )
            except Exception as e:
                self.stdout.write(f'ERROR: {e}')

        # 3) 집계
        if not results:
            self.stdout.write('\n결과 없음.')
            return

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('집계 결과')
        self.stdout.write(f'{"="*60}\n')

        # 자동 평가 점수
        n = len(results)
        ok_results = [r for r in results if not r.is_fallback]
        fb_results = [r for r in results if r.is_fallback]

        self.stdout.write(f'총 {n}건 | 성공 {len(ok_results)}건 | fallback {len(fb_results)}건')
        self.stdout.write(f'fallback 비율: {len(fb_results)/n*100:.1f}%\n')

        if ok_results:
            # 수치 보존율
            avg_strict = sum(r.numeric_fidelity_strict for r in ok_results) / len(ok_results)
            avg_semantic = sum(r.numeric_fidelity_semantic for r in ok_results) / len(ok_results)
            avg_total = sum(r.numeric_fidelity_total for r in ok_results) / len(ok_results)
            self.stdout.write(f'수치 보존율 (엄격): {avg_strict:.2%}')
            self.stdout.write(f'수치 보존율 (의미): {avg_semantic:.2%}')
            self.stdout.write(f'수치 보존율 (전체): {avg_total:.2%}\n')

            # 수치 환각
            avg_halluc = sum(r.numeric_hallucination_count for r in ok_results) / len(ok_results)
            max_halluc = max(r.numeric_hallucination_count for r in ok_results)
            self.stdout.write(f'수치 환각: 평균 {avg_halluc:.1f}건, 최대 {max_halluc}건\n')

            # JSON 준수
            json_ok = sum(1 for r in ok_results if r.json_compliant)
            self.stdout.write(f'JSON 준수율: {json_ok}/{len(ok_results)} ({json_ok/len(ok_results)*100:.0f}%)\n')

            # 응답시간
            totals = sorted(r.total_ms for r in ok_results)
            report_times = sorted(r.report_ms for r in ok_results)
            stats_times = sorted(r.stats_ms for r in ok_results)

            def percentile(arr, p):
                idx = int(len(arr) * p)
                return arr[min(idx, len(arr)-1)]

            self.stdout.write('응답시간 (전체 endpoint):')
            self.stdout.write(f'  p50={percentile(totals, 0.5):.0f}ms  p95={percentile(totals, 0.95):.0f}ms')
            self.stdout.write('응답시간 (OpenAI API):')
            self.stdout.write(f'  p50={percentile(report_times, 0.5):.0f}ms  p95={percentile(report_times, 0.95):.0f}ms')
            self.stdout.write('응답시간 (SQL stats):')
            self.stdout.write(f'  p50={percentile(stats_times, 0.5):.0f}ms  p95={percentile(stats_times, 0.95):.0f}ms')

            # TABLE별 브레이크다운
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write('TABLE별 상세')
            self.stdout.write(f'{"="*60}\n')

            for cat in sorted(set(r.case.category for r in ok_results)):
                cat_results = [r for r in ok_results if r.case.category == cat]
                if not cat_results:
                    continue
                avg_f = sum(r.numeric_fidelity_total for r in cat_results) / len(cat_results)
                avg_h = sum(r.numeric_hallucination_count for r in cat_results) / len(cat_results)
                avg_t = sum(r.total_ms for r in cat_results) / len(cat_results)
                self.stdout.write(
                    f'{cat:6s}: {len(cat_results)}건 | '
                    f'보존율={avg_f:.2%} | 환각={avg_h:.1f} | '
                    f'시간={avg_t:.0f}ms'
                )

            # 개별 상세 (수치 보존 실패 케이스)
            low_fidelity = [r for r in ok_results if r.numeric_fidelity_strict < 0.7]
            if low_fidelity:
                self.stdout.write(f'\n{"="*60}')
                self.stdout.write(f'엄격 보존율 < 70% 케이스 ({len(low_fidelity)}건)')
                self.stdout.write(f'{"="*60}\n')
                for r in low_fidelity:
                    self.stdout.write(
                        f'{r.case.bid_ntce_no} ({r.case.category}) '
                        f'strict={r.numeric_fidelity_strict:.2%} '
                        f'halluc={r.numeric_hallucination_count}'
                    )
                    self.stdout.write(f'  summary: {r.report_summary[:100]}...')

        # JSON 출력
        if options['json']:
            output = {
                'summary': {
                    'total': n,
                    'success': len(ok_results),
                    'fallback': len(fb_results),
                    'avg_fidelity_strict': round(avg_strict, 4) if ok_results else 0,
                    'avg_fidelity_semantic': round(avg_semantic, 4) if ok_results else 0,
                    'avg_fidelity_total': round(avg_total, 4) if ok_results else 0,
                    'avg_hallucination': round(avg_halluc, 1) if ok_results else 0,
                },
                'cases': [],
            }
            for r in results:
                output['cases'].append({
                    'ntce_no': r.case.bid_ntce_no,
                    'category': r.case.category,
                    'presume_price': r.case.presume_price,
                    'total_ms': r.total_ms,
                    'report_ms': r.report_ms,
                    'stats_ms': r.stats_ms,
                    'fidelity_strict': r.numeric_fidelity_strict,
                    'fidelity_semantic': r.numeric_fidelity_semantic,
                    'hallucination': r.numeric_hallucination_count,
                    'json_ok': r.json_compliant,
                    'is_fallback': r.is_fallback,
                    'similar_count': r.similar_count,
                    'report_summary': r.report_summary,
                    'report_strategy': r.report_strategy,
                })
            self.stdout.write(f'\n\n--- JSON ---\n{json.dumps(output, ensure_ascii=False, indent=2)}')
