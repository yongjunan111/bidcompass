"""G2B 공공데이터 API 클라이언트.

나라장터 입찰공고/낙찰/계약 3종 API를 호출하고 페이지네이션을 자동 처리한다.
"""

import asyncio
import os
from collections.abc import AsyncGenerator

import httpx

BASE_URL = "http://apis.data.go.kr/1230000/ao/PubDataOpnStdService"

ENDPOINTS = {
    "announcements": "getDataSetOpnStdBidPblancInfo",
    "winning_bids": "getDataSetOpnStdScsbidInfo",
    "contracts": "getDataSetOpnStdCntrctInfo",
}

NUM_OF_ROWS = 999
REQUEST_DELAY = 0.3  # 초 (rate limit 안전장치)


def get_api_key() -> str:
    key = os.getenv("API_KEY", "")
    if not key:
        raise RuntimeError("API_KEY 환경변수가 설정되지 않았습니다")
    return key


def extract_items(data: dict) -> list[dict]:
    """API 응답에서 items 리스트를 추출한다."""
    response_data = data.get("response", data)
    body = response_data.get("body", {})
    items = body.get("items", [])

    if isinstance(items, dict) and "item" in items:
        items_list = items["item"]
        return items_list if isinstance(items_list, list) else [items_list]
    return items if isinstance(items, list) else []


def get_total_count(data: dict) -> int:
    """API 응답에서 totalCount를 추출한다."""
    response_data = data.get("response", data)
    body = response_data.get("body", {})
    return int(body.get("totalCount", 0))


async def fetch_pages(
    endpoint_key: str,
    params: dict,
    callback=None,
) -> AsyncGenerator[list[dict], None]:
    """엔드포인트를 페이지네이션하며 배치 단위로 yield한다.

    Args:
        endpoint_key: ENDPOINTS 키 (announcements / winning_bids / contracts)
        params: 날짜 파라미터 등 요청 파라미터
        callback: 페이지마다 호출되는 콜백 (page_no, fetched_so_far, total_count)

    Yields:
        각 페이지의 items 리스트
    """
    api_key = get_api_key()
    endpoint = ENDPOINTS[endpoint_key]
    url = f"{BASE_URL}/{endpoint}"

    page_no = 1
    total_count = None
    fetched = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            request_params = {
                "ServiceKey": api_key,
                "type": "json",
                "numOfRows": NUM_OF_ROWS,
                "pageNo": page_no,
                **params,
            }

            resp = await client.get(url, params=request_params)
            resp.raise_for_status()
            data = resp.json()

            if total_count is None:
                total_count = get_total_count(data)

            items = extract_items(data)
            if not items:
                break

            fetched += len(items)

            if callback:
                callback(page_no, fetched, total_count)

            yield items

            if fetched >= total_count:
                break

            page_no += 1
            await asyncio.sleep(REQUEST_DELAY)
