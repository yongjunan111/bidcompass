"""[DEPRECATED] 나의방 낙찰 엑셀에서 공고번호를 추출하고 A값 + 복수예비가격을 API로 수집한다.

.. deprecated::
    엑셀 기반 수집 파이프라인. DB 기반 수집은 collect_bid_api_data를 사용하세요.
    이 커맨드는 하위 호환을 위해 유지되며, 향후 삭제될 수 있습니다.

사용:
    python manage.py collect_bid_data              # 전체 수집
    python manage.py collect_bid_data --limit 5    # 테스트 (5건만)
    python manage.py collect_bid_data --skip-a-value  # 복수예비가격만
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx
from django.core.management.base import BaseCommand

from g2b.services.g2b_client import REQUEST_DELAY, extract_items, get_api_key

# 엑셀 파일 경로 (docs/ 하위)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
EXCEL_FILES = [
    BASE_DIR / "docs" / "나의방_낙찰2026-02- 2025.xlsx",
    BASE_DIR / "docs" / "나의방_낙찰2026-02-05_1.xlsx",
]
OUTPUT_DIR = BASE_DIR / "data" / "collected"

# API 엔드포인트
BID_INFO_BASE = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
AWARD_INFO_BASE = "https://apis.data.go.kr/1230000/as/ScsbidInfoService"

# A값 7개 항목 필드명
A_VALUE_FIELDS = [
    "npnInsrprm",           # 국민연금
    "mrfnHealthInsrprm",    # 건강보험
    "rtrfundNon",           # 퇴직공제
    "odsnLngtrmrcprInsrprm",  # 장기요양
    "sftyMngcst",           # 산업안전
    "sftyChckMngcst",       # 안전관리
    "qltyMngcst",           # 품질관리
]


def parse_bid_numbers(excel_paths: list[Path]) -> list[tuple[str, str]]:
    """엑셀 파일에서 공고번호를 추출하여 (bidNtceNo, bidNtceOrd) 리스트 반환."""
    import openpyxl

    seen = set()
    result = []

    for path in excel_paths:
        if not path.exists():
            raise FileNotFoundError(f"엑셀 파일 없음: {path}")

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active

        # 헤더: row 2, 데이터: row 3~, 공고번호: D열 (4번째)
        for row in ws.iter_rows(min_row=3, min_col=4, max_col=4, values_only=True):
            raw = row[0]
            if not raw:
                continue
            raw = str(raw).strip()

            # 차수 분리: 끝이 "-N~NNN" (1~3자리 숫자)이면 차수로 분리
            # 예: "R25BK01238858-000" → ("R25BK01238858", "000")
            # 예: "2025-01-000177-00" → ("2025-01-000177", "00")
            # 예: "E012508562-2"      → ("E012508562", "2")
            # 예: "2025-27148"        → 전체가 공고번호 (5자리 → 분리 안함)
            parts = raw.rsplit("-", 1)
            if len(parts) == 2 and 1 <= len(parts[1]) <= 3 and parts[1].isdigit():
                ntce_no, ntce_ord = parts
            else:
                ntce_no, ntce_ord = raw, ""

            key = (ntce_no, ntce_ord)
            if key not in seen:
                seen.add(key)
                result.append(key)

        wb.close()

    return result


async def call_api(
    client: httpx.AsyncClient,
    base_url: str,
    operation: str,
    params: dict,
) -> dict:
    """API 호출 후 JSON 반환. 에러 시 _error 키 포함 dict."""
    url = f"{base_url}/{operation}"
    try:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return {"_error": resp.status_code}
        return resp.json()
    except httpx.RequestError as e:
        return {"_error": f"network({type(e).__name__})"}
    except Exception:
        return {"_error": "json_parse"}


async def collect_all(
    bid_numbers: list[tuple[str, str]],
    api_key: str,
    skip_a_value: bool,
    stdout,
    style,
) -> tuple[dict, dict, dict]:
    """모든 공고에 대해 A값 + 복수예비가격 수집."""
    a_values = {}
    prelim_prices = {}
    stats = {
        "total": len(bid_numbers),
        "a_value_ok": 0,
        "a_value_empty": 0,
        "a_value_error": 0,
        "a_value_skipped": 0,
        "prelim_ok": 0,
        "prelim_empty": 0,
        "prelim_error": 0,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, (ntce_no, ntce_ord) in enumerate(bid_numbers, 1):
            display_no = f"{ntce_no}-{ntce_ord}" if ntce_ord else ntce_no
            a_status = ""
            p_status = ""

            # ── A값 ──
            if skip_a_value:
                a_status = "skip (--skip-a-value)"
                stats["a_value_skipped"] += 1
            else:
                a_params = {
                    "ServiceKey": api_key,
                    "type": "json",
                    "numOfRows": 10,
                    "pageNo": 1,
                    "inqryDiv": "2",
                    "bidNtceNo": ntce_no,
                }
                data = await call_api(
                    client, BID_INFO_BASE,
                    "getBidPblancListBidPrceCalclAInfo", a_params,
                )

                if "_error" in data:
                    a_status = f"error({data['_error']})"
                    stats["a_value_error"] += 1
                else:
                    items = extract_items(data)
                    if items:
                        a_values[display_no] = items
                        field_count = sum(
                            1 for f in A_VALUE_FIELDS
                            if items[0].get(f)
                        )
                        a_status = f"OK ({field_count}항목)"
                        stats["a_value_ok"] += 1
                    else:
                        a_status = "empty (비대상)"
                        stats["a_value_empty"] += 1

                await asyncio.sleep(REQUEST_DELAY)

            # ── 복수예비가격 ──
            # 차수가 있으면 그대로, 없으면 빈값 먼저 → 실패 시 000 fallback
            ord_candidates = [ntce_ord] if ntce_ord else ["", "000"]
            for ord_try in ord_candidates:
                p_params = {
                    "ServiceKey": api_key,
                    "type": "json",
                    "numOfRows": 20,
                    "pageNo": 1,
                    "inqryDiv": "2",
                    "bidNtceNo": ntce_no,
                    "bidNtceOrd": ord_try,
                }
                data = await call_api(
                    client, AWARD_INFO_BASE,
                    "getOpengResultListInfoCnstwkPreparPcDetail", p_params,
                )

                if "_error" not in data:
                    items = extract_items(data)
                    if items:
                        prelim_prices[display_no] = items
                        p_status = f"OK ({len(items)}개)"
                        stats["prelim_ok"] += 1
                        break
                # fallback 시도 전 대기
                await asyncio.sleep(REQUEST_DELAY)
            else:
                # 모든 시도 실패
                if "_error" in data:
                    p_status = f"error({data['_error']})"
                    stats["prelim_error"] += 1
                else:
                    p_status = "없음 (비복수예가)"
                    stats["prelim_empty"] += 1

            await asyncio.sleep(REQUEST_DELAY)

            # 진행상황 출력
            stdout.write(
                f"[{i:>3}/{stats['total']}] {display_no:25s}: "
                f"A값 {a_status:20s} | 복수예비가격 {p_status}"
            )

    return a_values, prelim_prices, stats


class Command(BaseCommand):
    help = "[DEPRECATED] 나의방 낙찰 엑셀 공고번호로 A값 + 복수예비가격 API 수집 → collect_bid_api_data 사용"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=0,
            help="수집 건수 제한 (테스트용, 0=전체)",
        )
        parser.add_argument(
            "--skip-a-value", action="store_true",
            help="A값 API 호출 생략 (404일 때 복수예비가격만 수집)",
        )

    def handle(self, *args, **options):
        self.stderr.write(self.style.WARNING(
            "[DEPRECATED] collect_bid_data는 폐기 예정입니다. "
            "collect_bid_api_data를 사용하세요."
        ))
        limit = options["limit"]
        skip_a_value = options["skip_a_value"]

        # 1. 엑셀에서 공고번호 추출
        self.stdout.write("엑셀 파일에서 공고번호 추출 중...")
        bid_numbers = parse_bid_numbers(EXCEL_FILES)
        self.stdout.write(f"나의방 공고 {len(bid_numbers)}건 로드 완료")

        if limit > 0:
            bid_numbers = bid_numbers[:limit]
            self.stdout.write(f"  --limit {limit} 적용: {len(bid_numbers)}건 수집")

        # 2. API 수집
        api_key = get_api_key()
        a_values, prelim_prices, stats = asyncio.run(
            collect_all(bid_numbers, api_key, skip_a_value, self.stdout, self.style)
        )

        # 3. JSON 저장
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if a_values:
            a_path = OUTPUT_DIR / "a_values.json"
            a_path.write_text(
                json.dumps(a_values, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.stdout.write(f"A값 저장: {a_path} ({len(a_values)}건)")

        if prelim_prices:
            p_path = OUTPUT_DIR / "preliminary_prices.json"
            p_path.write_text(
                json.dumps(prelim_prices, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.stdout.write(f"복수예비가격 저장: {p_path} ({len(prelim_prices)}건)")

        log = {
            "timestamp": timestamp,
            "total": stats["total"],
            "a_value": {
                "ok": stats["a_value_ok"],
                "empty": stats["a_value_empty"],
                "error": stats["a_value_error"],
                "skipped": stats["a_value_skipped"],
            },
            "preliminary_prices": {
                "ok": stats["prelim_ok"],
                "empty": stats["prelim_empty"],
                "error": stats["prelim_error"],
            },
        }
        log_path = OUTPUT_DIR / "collection_log.json"
        log_path.write_text(
            json.dumps(log, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 4. 요약 출력
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"완료: A값 {stats['a_value_ok']}/{stats['total']} | "
                f"복수예비가격 {stats['prelim_ok']}/{stats['total']} | "
                f"실패 {stats['a_value_error'] + stats['prelim_error']}건"
            )
        )
        self.stdout.write(f"로그: {log_path}")
