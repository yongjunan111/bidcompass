"""입찰공고정보서비스 + 낙찰정보서비스 API 필드 탐색.

공식문서 기반 URL:
- 입찰공고정보서비스: apis.data.go.kr/1230000/ad/BidPublicInfoService
- 낙찰정보서비스:     apis.data.go.kr/1230000/as/ScsbidInfoService

Run: cd ~/Desktop/toyproject/bidcompass && python test_new_apis.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")

# 공식문서 기준 URL
BID_INFO_BASE = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"  # 아직 404 (승인 반영 대기)
AWARD_INFO_BASE = "https://apis.data.go.kr/1230000/as/ScsbidInfoService"  # 작동 확인!


async def call_api(base_url: str, operation: str, params: dict) -> dict:
    if not API_KEY:
        print("ERROR: API_KEY not set in .env")
        sys.exit(1)

    url = f"{base_url}/{operation}"
    request_params = {"ServiceKey": API_KEY, "type": "json", **params}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=request_params)
        print(f"\n  HTTP {resp.status_code} | {operation}")
        if resp.status_code != 200:
            print(f"  Response: {resp.text[:300]}")
            return {}
        try:
            return resp.json()
        except Exception:
            print(f"  Non-JSON: {resp.text[:300]}")
            return {}


def extract_items(data: dict) -> list:
    response_data = data.get("response", data)
    body = response_data.get("body", {})
    items = body.get("items", [])
    if isinstance(items, dict) and "item" in items:
        items_list = items["item"]
        return items_list if isinstance(items_list, list) else [items_list]
    return items if isinstance(items, list) else []


def print_result(data: dict, label: str):
    print(f"\n{'='*80}")
    print(f"  {label}")
    print(f"{'='*80}")

    if not data:
        print("  (빈 응답)")
        return []

    response_data = data.get("response", data)
    header = response_data.get("header", {})
    body = response_data.get("body", {})

    result_code = header.get("resultCode")
    result_msg = header.get("resultMsg")
    print(f"  resultCode: {result_code} | resultMsg: {result_msg}")
    print(f"  totalCount: {body.get('totalCount')}")

    items = extract_items(data)
    print(f"  items: {len(items)}건")

    if items:
        first = items[0]
        print(f"\n  [첫 번째 항목 - {len(first)}개 필드]")
        for k, v in first.items():
            val_str = str(v)[:70] if v else "(empty)"
            marker = " <<<" if v and str(v).strip() else ""
            print(f"    {k:45s} = {val_str}{marker}")
    else:
        print("  (항목 없음)")

    return items


async def main():
    print("=" * 80)
    print("  G2B 신규 API 필드 탐색기 (공식문서 URL)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  입찰공고정보: {BID_INFO_BASE}")
    print(f"  낙찰정보:     {AWARD_INFO_BASE}")
    print("=" * 80)

    now = datetime.now()
    week_ago = (now - timedelta(days=7)).strftime("%Y%m%d") + "0000"
    now_str = now.strftime("%Y%m%d") + "2359"

    # ── 1. 공사 공고 목록 (공고번호 확보) ──
    data = await call_api(BID_INFO_BASE, "getBidPblancListInfoCnstwkPPSSrch", {
        "inqryBgnDt": week_ago,
        "inqryEndDt": now_str,
        "numOfRows": 3,
        "pageNo": 1,
        "inqryDiv": "1",
    })
    items = print_result(data, "1. 입찰공고정보서비스 - 공사 공고목록")

    bid_ntce_no = ""
    bid_ntce_ord = ""
    if items:
        bid_ntce_no = items[0].get("bidNtceNo", "")
        bid_ntce_ord = items[0].get("bidNtceOrd", "000")
        print(f"\n  >> 공고번호: {bid_ntce_no} (차수: {bid_ntce_ord})")

    # ── 2. 개찰결과 공사 (openg_no 확보 — A값 조회에 필요) ──
    data = await call_api(AWARD_INFO_BASE, "getOpengResultListInfoCnstwkPPSSrch", {
        "inqryBgnDt": week_ago,
        "inqryEndDt": now_str,
        "numOfRows": 3,
        "pageNo": 1,
        "inqryDiv": "1",
    })
    opening_items = print_result(data, "2. 낙찰정보서비스 - 개찰결과 공사")

    openg_no = ""
    openg_ord = ""
    if opening_items:
        openg_no = opening_items[0].get("bidNtceNo", "")
        openg_ord = opening_items[0].get("bidNtceOrd", "000")
        print(f"\n  >> 개찰 공고번호: {openg_no} (차수: {openg_ord})")

    # ── 3. ★ A값 산식 정보 (핵심!) ──
    # 기간 조회: 7일 (30일은 입력범위값 초과 에러)
    a_params = {"numOfRows": 5, "pageNo": 1, "inqryDiv": "1",
                "inqryBgnDt": week_ago,
                "inqryEndDt": now_str}
    data = await call_api(BID_INFO_BASE, "getBidPblancListBidPrceCalclAInfo", a_params)
    if data and not extract_items(data):
        import json
        print(f"\n  [DEBUG] A값 raw JSON (첫 500자):\n  {json.dumps(data, ensure_ascii=False)[:500]}")
    print_result(data, "3. ★ A값 산식 - 기간조회 (7일)")

    # 개찰결과 공고번호로 조회 (적격심사 건)
    lookup_no = openg_no or bid_ntce_no
    if lookup_no:
        data2 = await call_api(BID_INFO_BASE, "getBidPblancListBidPrceCalclAInfo", {
            "numOfRows": 5, "pageNo": 1, "inqryDiv": "2",
            "bidNtceNo": lookup_no,
        })
        print_result(data2, f"3-1. ★ A값 산식 (공고번호: {lookup_no})")

    # ── 4. 공사 기초금액 ──
    if lookup_no:
        data = await call_api(BID_INFO_BASE, "getBidPblancListInfoCnstwkBsisAmount", {
            "numOfRows": 5, "pageNo": 1, "inqryDiv": "2",
            "bidNtceNo": lookup_no,
        })
        print_result(data, f"4. 공사 기초금액 (공고번호: {lookup_no})")

    # ── 5. ★ 예비가격상세 (복수예비가격 15개) ──
    if openg_no:
        data = await call_api(AWARD_INFO_BASE, "getOpengResultListInfoCnstwkPreparPcDetail", {
            "numOfRows": 15, "pageNo": 1, "inqryDiv": "2",
            "bidNtceNo": openg_no, "bidNtceOrd": openg_ord,
        })
        print_result(data, "5. ★ 예비가격상세 (복수예비가격)")

    # ── 6. 낙찰 목록 공사 ──
    data = await call_api(AWARD_INFO_BASE, "getScsbidListSttusCnstwkPPSSrch", {
        "inqryBgnDt": week_ago,
        "inqryEndDt": now_str,
        "numOfRows": 3,
        "pageNo": 1,
        "inqryDiv": "1",
    })
    print_result(data, "6. 낙찰 목록 공사")

    print(f"\n{'='*80}")
    print("  완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
