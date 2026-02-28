"""G2B API response structure explorer.

Run: API_KEY=your_key python test_api.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta

import httpx
import xmltodict


BASE_URL = "http://apis.data.go.kr/1230000/ao/PubDataOpnStdService"

ENDPOINTS = {
    "bid_announcements": "getDataSetOpnStdBidPblancInfo",
    "successful_bids": "getDataSetOpnStdScsbidInfo",
    "contracts": "getDataSetOpnStdCntrctInfo",
}


async def call_api(endpoint: str, params: dict) -> dict:
    """Call G2B API and return raw response."""
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("ERROR: API_KEY environment variable not set")
        print("Get one at: https://www.data.go.kr/data/15129394/openapi.do")
        sys.exit(1)

    url = f"{BASE_URL}/{endpoint}"
    request_params = {"ServiceKey": api_key, "type": "json", **params}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=request_params)
        resp.raise_for_status()
        return resp.json()


def extract_items(data: dict) -> list:
    """Extract items list from API response."""
    response_data = data.get("response", data)
    body = response_data.get("body", {})
    items = body.get("items", [])

    if isinstance(items, dict) and "item" in items:
        items_list = items["item"]
        return items_list if isinstance(items_list, list) else [items_list]
    return items if isinstance(items, list) else []


def print_response_structure(data: dict, label: str):
    """Print response structure analysis."""
    print(f"\n{'='*80}")
    print(f"  {label}")
    print(f"{'='*80}")

    response_data = data.get("response", data)
    header = response_data.get("header", {})
    body = response_data.get("body", {})

    print(f"\n[Header]")
    print(f"  resultCode: {header.get('resultCode')}")
    print(f"  resultMsg:  {header.get('resultMsg')}")

    print(f"\n[Body meta]")
    print(f"  totalCount: {body.get('totalCount')}")
    print(f"  pageNo:     {body.get('pageNo')}")
    print(f"  numOfRows:  {body.get('numOfRows')}")

    items = extract_items(data)
    print(f"\n[Items] count={len(items)}")

    if items:
        first = items[0]
        print(f"\n[First item - all fields]")
        for k, v in first.items():
            val_preview = str(v)[:60] if v else "(empty)"
            print(f"  {k:40s} = {val_preview}")

        # Non-null fields summary
        non_null = {k: v for k, v in first.items() if v and str(v).strip()}
        print(f"\n[Non-null fields: {len(non_null)}/{len(first)}]")

    return items


async def test_bid_announcements():
    """Test 1: 입찰공고정보 - search recent construction bids."""
    now = datetime.now()
    start = (now - timedelta(days=7)).strftime("%Y%m%d0000")
    end = now.strftime("%Y%m%d2359")

    data = await call_api(ENDPOINTS["bid_announcements"], {
        "bidNtceBgnDt": start,
        "bidNtceEndDt": end,
        "numOfRows": 3,
        "pageNo": 1,
    })
    return print_response_structure(data, "1. 입찰공고정보 (Bid Announcements) - 최근 7일")


async def test_successful_bids():
    """Test 2: 낙찰정보 - search recent construction successful bids."""
    now = datetime.now()
    start = (now - timedelta(days=7)).strftime("%Y%m%d0000")
    end = now.strftime("%Y%m%d2359")

    data = await call_api(ENDPOINTS["successful_bids"], {
        "bsnsDivCd": "3",  # construction
        "opengBgnDt": start,
        "opengEndDt": end,
        "numOfRows": 3,
        "pageNo": 1,
    })
    return print_response_structure(data, "2. 낙찰정보 (Successful Bids) - 공사, 최근 7일")


async def test_contracts():
    """Test 3: 계약정보 - search recent contracts."""
    now = datetime.now()
    start = (now - timedelta(days=7)).strftime("%Y%m%d")
    end = now.strftime("%Y%m%d")

    data = await call_api(ENDPOINTS["contracts"], {
        "cntrctCnclsBgnDate": start,
        "cntrctCnclsEndDate": end,
        "numOfRows": 3,
        "pageNo": 1,
    })
    return print_response_structure(data, "3. 계약정보 (Contracts) - 최근 7일")


async def test_volume_check():
    """Test 4: Check total volume for construction bids in recent month."""
    now = datetime.now()
    start = (now - timedelta(days=30)).strftime("%Y%m%d0000")
    end = now.strftime("%Y%m%d2359")

    data = await call_api(ENDPOINTS["bid_announcements"], {
        "bidNtceBgnDt": start,
        "bidNtceEndDt": end,
        "numOfRows": 1,
        "pageNo": 1,
    })

    response_data = data.get("response", data)
    body = response_data.get("body", {})
    total = body.get("totalCount", 0)
    print(f"\n{'='*80}")
    print(f"  4. 최근 30일 입찰공고 총 건수: {total}")
    print(f"{'='*80}")
    return total


async def main():
    print("G2B API Response Structure Explorer")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"API Key: {os.getenv('API_KEY', 'NOT SET')[:8]}...")

    # Run all tests
    await test_bid_announcements()
    await test_successful_bids()
    await test_contracts()
    await test_volume_check()

    print(f"\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
