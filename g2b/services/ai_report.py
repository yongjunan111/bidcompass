"""BC-53: AI 전략 리포트 생성.

사전 추천 결과를 AI가 해설하는 리포트.
OpenAI API(httpx 직접 호출)로 생성, SDK 의존성 없음.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import List

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class ReportInput:
    table_name: str
    presume_price: int
    a_value: int
    floor_rate: str
    floor_bid: int
    band_low: int
    band_high: int
    base_bid: int
    safe_bid: int
    aggressive_bid: int
    similar_stats: dict


@dataclass
class ReportOutput:
    summary: str
    strategy: str
    risk_factors: List[str]
    evidence: List[str]
    action_items: List[str]


SYSTEM_PROMPT = """당신은 한국 공공조달(나라장터/G2B) 적격심사 전문 컨설턴트입니다.

역할:
- 사전 투찰 추천 결과를 바탕으로 전략 리포트를 작성합니다.
- 숫자(금액, 점수, 확률)는 절대 변경하지 마세요. 입력 데이터 그대로 인용하세요.
- 이 추천은 개찰 전 사전 분석이며, 유사 공고 통계와 가격점수 구조를 근거로 합니다.
- 한국어로 작성하세요.

반드시 아래 JSON 형식으로만 응답하세요:
{
  "summary": "2~3문장 요약",
  "strategy": "추천 전략 설명 (3~5문장)",
  "risk_factors": ["리스크1", "리스크2", ...],
  "evidence": ["근거1", "근거2", ...],
  "action_items": ["액션1", "액션2", ...]
}"""


def _build_user_prompt(inp: ReportInput) -> str:
    stats = inp.similar_stats
    return f"""## 공고 정보

- 별표 유형: {inp.table_name}
- 추정가격: {inp.presume_price:,}원
- A값: {inp.a_value:,}원
- 낙찰하한율: {inp.floor_rate}%
- 하한 최소 투찰가: {inp.floor_bid:,}원

## 사전 추천 결과

- 기본 추천 (Base): {inp.base_bid:,}원
- 보수적 (Safe): {inp.safe_bid:,}원
- 공격적 (Aggressive): {inp.aggressive_bid:,}원
- 추천 밴드: {inp.band_low:,}원 ~ {inp.band_high:,}원

## 유사공고 통계 ({stats.get('count', 0)}건)
- 평균 참여업체수: {stats.get('avg_bidder_cnt', 0)}개사
- 낙찰률 분포: P10={stats.get('p10_rate', 0):.4f}, P50={stats.get('p50_rate', 0):.4f}, P90={stats.get('p90_rate', 0):.4f}

위 사전 추천 데이터를 기반으로 입찰 전략 리포트를 작성해주세요.
이 추천은 개찰 전 사전 분석이며, 최종 투찰 결정은 입찰자의 책임입니다."""


def generate_report(inp: ReportInput) -> ReportOutput:
    """OpenAI API로 전략 리포트 생성.

    API 키 미설정 또는 호출 실패 시 fallback 텍스트 반환.
    """
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        return _fallback_report(inp, reason="OPENAI_API_KEY 미설정")

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(inp)},
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        content = json.loads(data["choices"][0]["message"]["content"])
        return ReportOutput(
            summary=content.get("summary", ""),
            strategy=content.get("strategy", ""),
            risk_factors=content.get("risk_factors", []),
            evidence=content.get("evidence", []),
            action_items=content.get("action_items", []),
        )
    except Exception as e:
        logger.warning("AI report generation failed: %s", e)
        return _fallback_report(inp, reason=str(e))


def _fallback_report(inp: ReportInput, reason: str = "") -> ReportOutput:
    """API 실패 시 규칙 기반 fallback 리포트."""
    stats = inp.similar_stats
    count = stats.get("count", 0)

    summary = (
        f"{inp.table_name} 공고 (추정가격 {inp.presume_price:,}원) 사전 분석 결과입니다. "
        f"유사공고 {count}건 통계를 참고하세요."
    )
    strategy = (
        f"기본 추천 투찰금액 {inp.base_bid:,}원을 중심으로, "
        f"하한율 {inp.floor_rate}% 통과를 반드시 확인하세요. "
        f"추천 밴드: {inp.band_low:,}원 ~ {inp.band_high:,}원."
    )

    return ReportOutput(
        summary=summary,
        strategy=strategy,
        risk_factors=[
            "AI 리포트 생성 불가 — 규칙 기반 요약만 제공",
            f"원인: {reason}" if reason else "원인 불명",
        ],
        evidence=[f"유사공고 {count}건 통계 기반", "가격점수 구조 기반 사전 추천"],
        action_items=["하한율 통과 확인", "최종 투찰 결정은 입찰자 책임"],
    )
