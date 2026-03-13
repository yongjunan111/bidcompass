from __future__ import annotations

import os
import time
from typing import Any

import httpx

BID_INFO_BASE = 'https://apis.data.go.kr/1230000/ad/BidPublicInfoService'
AWARD_INFO_BASE = 'https://apis.data.go.kr/1230000/as/ScsbidInfoService'
GENERIC_BASE = 'https://apis.data.go.kr/1230000/ao/PubDataOpnStdService'
DEFAULT_PAGE_SIZE = 100
REQUEST_DELAY = 0.2


def get_api_key() -> str:
    api_key = os.getenv('API_KEY', '').strip()
    if not api_key:
        raise RuntimeError('API_KEY 환경변수가 설정되지 않았습니다.')
    return api_key


def extract_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    response_data = data.get('response', data)
    body = response_data.get('body', {})
    items = body.get('items', [])
    if isinstance(items, dict) and 'item' in items:
        item_value = items['item']
        return item_value if isinstance(item_value, list) else [item_value]
    return items if isinstance(items, list) else []


def get_total_count(data: dict[str, Any]) -> int:
    response_data = data.get('response', data)
    body = response_data.get('body', {})
    return int(body.get('totalCount', 0) or 0)


def request_json(
    *,
    base_url: str,
    operation: str,
    params: dict[str, Any],
    client: httpx.Client,
) -> dict[str, Any]:
    url = f'{base_url}/{operation}'
    response = client.get(
        url,
        params={
            'ServiceKey': get_api_key(),
            'type': 'json',
            **params,
        },
    )
    response.raise_for_status()
    return response.json()


def fetch_paged_items(
    *,
    base_url: str,
    operation: str,
    params: dict[str, Any],
    callback=None,
    limit: int | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page_no = 1
    total_count = 0

    with httpx.Client(timeout=30.0) as client:
        while True:
            data = request_json(
                base_url=base_url,
                operation=operation,
                params={
                    **params,
                    'numOfRows': page_size,
                    'pageNo': page_no,
                },
                client=client,
            )
            if total_count == 0:
                total_count = get_total_count(data)

            page_items = extract_items(data)
            if not page_items:
                break

            items.extend(page_items)
            if callback:
                callback(page_no, len(items), total_count)

            if limit and len(items) >= limit:
                return items[:limit]
            if len(items) >= total_count:
                break

            page_no += 1
            time.sleep(REQUEST_DELAY)

    return items


def fetch_construction_notices(
    *,
    start_datetime: str,
    end_datetime: str,
    limit: int | None = None,
    callback=None,
) -> list[dict[str, Any]]:
    return fetch_paged_items(
        base_url=BID_INFO_BASE,
        operation='getBidPblancListInfoCnstwkPPSSrch',
        params={
            'inqryDiv': '1',
            'inqryBgnDt': start_datetime,
            'inqryEndDt': end_datetime,
        },
        limit=limit,
        callback=callback,
    )


def fetch_construction_successful_bids(
    *,
    start_datetime: str,
    end_datetime: str,
    limit: int | None = None,
    callback=None,
) -> list[dict[str, Any]]:
    return fetch_paged_items(
        base_url=AWARD_INFO_BASE,
        operation='getScsbidListSttusCnstwkPPSSrch',
        params={
            'inqryDiv': '1',
            'inqryBgnDt': start_datetime,
            'inqryEndDt': end_datetime,
        },
        limit=limit,
        callback=callback,
    )


def fetch_construction_a_value(bid_ntce_no: str) -> dict[str, Any] | None:
    with httpx.Client(timeout=30.0) as client:
        data = request_json(
            base_url=BID_INFO_BASE,
            operation='getBidPblancListBidPrceCalclAInfo',
            params={
                'inqryDiv': '2',
                'bidNtceNo': bid_ntce_no,
                'numOfRows': 5,
                'pageNo': 1,
            },
            client=client,
        )
    items = extract_items(data)
    return items[0] if items else None


def fetch_construction_base_amount(bid_ntce_no: str) -> dict[str, Any] | None:
    with httpx.Client(timeout=30.0) as client:
        data = request_json(
            base_url=BID_INFO_BASE,
            operation='getBidPblancListInfoCnstwkBsisAmount',
            params={
                'inqryDiv': '2',
                'bidNtceNo': bid_ntce_no,
                'numOfRows': 5,
                'pageNo': 1,
            },
            client=client,
        )
    items = extract_items(data)
    return items[0] if items else None


def fetch_construction_prelim_prices(
    bid_ntce_no: str,
    bid_ntce_ord: str,
) -> list[dict[str, Any]]:
    with httpx.Client(timeout=30.0) as client:
        data = request_json(
            base_url=AWARD_INFO_BASE,
            operation='getOpengResultListInfoCnstwkPreparPcDetail',
            params={
                'inqryDiv': '2',
                'bidNtceNo': bid_ntce_no,
                'bidNtceOrd': bid_ntce_ord,
                'numOfRows': 20,
                'pageNo': 1,
            },
            client=client,
        )
    return extract_items(data)


def fetch_construction_contracts(
    *,
    start_date: str,
    end_date: str,
    limit: int | None = None,
    callback=None,
) -> list[dict[str, Any]]:
    return fetch_paged_items(
        base_url=GENERIC_BASE,
        operation='getDataSetOpnStdCntrctInfo',
        params={
            'inqryDiv': '1',
            'cntrctCnclsBgnDate': start_date,
            'cntrctCnclsEndDate': end_date,
        },
        limit=limit,
        callback=callback,
    )
