"""BC-31/36: DB 기반 A값 + 복수예비가격 API 수집.

BidResult에서 적격심사 건설 <100억 공고를 추출하고,
입찰공고정보서비스(A값) + 낙찰정보서비스(복수예비가격) API로 수집하여 DB에 저장한다.

아키텍처: API → JSON 원본 저장 → DB 적재 (2단계)
  - JSON 원본: data/collected/api_raw/{a_values,prelim_prices}/{ntce_no}_{ntce_ord}.json
  - DB 손실 시 JSON에서 재적재 가능 (load_api_json 커맨드)

BC-36 안전장치:
  - PID lockfile: 중복 실행 방지 (O_CREAT|O_EXCL 원자적 생성)
  - RateLimitError: 429 / API 한도 초과 즉시 중단
  - 연속 에러 5회 자동 중단

사용:
    python manage.py collect_bid_api_data                    # 기본 1000건
    python manage.py collect_bid_api_data --limit 5          # 테스트
    python manage.py collect_bid_api_data --daily-limit 900  # 일일 한도 조절
    python manage.py collect_bid_api_data --skip-a-value     # 복수예비가격만
    python manage.py collect_bid_api_data --skip-prelim      # A값만
    python manage.py collect_bid_api_data --force             # 재수집
"""

import atexit
import json
import os
import sys
import time
from pathlib import Path

import httpx
from django.core.management.base import BaseCommand

from g2b.models import (
    BidApiAValue,
    BidApiCollectionLog,
    BidApiPrelimPrice,
    BidResult,
)
from g2b.services.g2b_client import REQUEST_DELAY, extract_items, get_api_key

# API 엔드포인트
BID_INFO_BASE = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
AWARD_INFO_BASE = "https://apis.data.go.kr/1230000/as/ScsbidInfoService"

# 100억 (원)
MAX_PRESUME_PRICE = 10_000_000_000

# BC-36: 안전장치 상수
LOCK_FILE = "/tmp/collect_bid_api_data.lock"
MAX_CONSECUTIVE_ERRORS = 5

# JSON 원본 저장 경로
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "collected" / "api_raw"
RAW_A_VALUE_DIR = RAW_DIR / "a_values"
RAW_PRELIM_DIR = RAW_DIR / "prelim_prices"

# A값 API 필드 → 모델 필드 매핑
A_VALUE_API_TO_MODEL = {
    "npnInsrprm": "national_pension",
    "mrfnHealthInsrprm": "health_insurance",
    "rtrfundNon": "retirement_mutual_aid",
    "odsnLngtrmrcprInsrprm": "long_term_care",
    "sftyMngcst": "occupational_safety",
    "sftyChckMngcst": "safety_management",
    "qltyMngcst": "quality_management",
}


# ──────────────────────────────────────────────
# BC-36: RateLimitError
# ──────────────────────────────────────────────

class RateLimitError(Exception):
    """429 또는 API 일일한도 초과 시 raise."""


# ──────────────────────────────────────────────
# BC-36: PID 기반 Lockfile
# ──────────────────────────────────────────────

class PidLock:
    """PID 기반 lockfile. O_CREAT|O_EXCL로 원자적 생성."""

    def __init__(self, path: str = LOCK_FILE):
        self.path = path
        self._fd = None

    def acquire(self) -> bool:
        """Lock 획득 시도. 성공 True, 실패 False."""
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            self._fd = True
            atexit.register(self.release)
            return True
        except FileExistsError:
            # 기존 PID 확인
            return self._check_stale_and_retry()

    def _check_stale_and_retry(self) -> bool:
        """기존 lock의 PID가 죽었으면 제거 후 1회 재시도."""
        try:
            with open(self.path) as f:
                old_pid = int(f.read().strip())
        except (ValueError, OSError):
            # 파일 읽기 실패 → stale로 간주
            self._force_remove()
            return self._retry_once()

        # PID 살아있는지 확인
        try:
            os.kill(old_pid, 0)
            # 살아있음 → 실제 중복 실행
            return False
        except ProcessLookupError:
            # 죽은 프로세스 → stale lock
            self._force_remove()
            return self._retry_once()
        except PermissionError:
            # 권한 부족이지만 프로세스 존재 → 중복 실행
            return False

    def _retry_once(self) -> bool:
        """stale lock 제거 후 1회 재시도."""
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            self._fd = True
            atexit.register(self.release)
            return True
        except FileExistsError:
            return False

    def _force_remove(self):
        try:
            os.remove(self.path)
        except OSError:
            pass

    def release(self):
        """본인 PID일 때만 lock 해제."""
        if not self._fd:
            return
        try:
            with open(self.path) as f:
                stored_pid = int(f.read().strip())
            if stored_pid == os.getpid():
                os.remove(self.path)
        except (ValueError, OSError):
            pass
        self._fd = None


def call_api(
    client: httpx.Client,
    base_url: str,
    operation: str,
    params: dict,
) -> dict:
    """API 호출 후 JSON 반환. 429/한도 초과 시 RateLimitError raise."""
    url = f"{base_url}/{operation}"
    try:
        resp = client.get(url, params=params)

        # BC-36: HTTP 429 즉시 중단
        if resp.status_code == 429:
            raise RateLimitError("HTTP 429 Too Many Requests")

        if resp.status_code != 200:
            return {"_error": f"http_{resp.status_code}"}

        data = resp.json()

        # BC-36: HTTP 200이지만 API 내부 한도 초과 체크
        header = data.get("response", {}).get("header", {})
        result_code = header.get("resultCode", "00")
        result_msg = header.get("resultMsg", "")
        if result_code != "00" and "한도" in result_msg:
            raise RateLimitError(f"API 한도 초과: {result_msg}")

        return data
    except RateLimitError:
        raise
    except httpx.RequestError as e:
        return {"_error": f"network({type(e).__name__})"}
    except Exception:
        return {"_error": "json_parse"}


def parse_api_int(val) -> int:
    """API 응답의 숫자 문자열 → int. 소수점 포함 시 절삭. 빈값/None → 0."""
    if val is None:
        return 0
    s = str(val).strip()
    if not s:
        return 0
    return int(float(s))


class Command(BaseCommand):
    help = "BC-31/36: DB 기반 A값 + 복수예비가격 API 수집"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=1000,
            help="수집 대상 공고 수 (기본 1000)",
        )
        parser.add_argument(
            "--daily-limit", type=int, default=900,
            help="일일 API 호출 한도 (안전 마진, 기본 900)",
        )
        parser.add_argument(
            "--skip-a-value", action="store_true",
            help="A값 API 수집 생략",
        )
        parser.add_argument(
            "--skip-prelim", action="store_true",
            help="복수예비가격 API 수집 생략",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="이미 수집된 건도 재수집",
        )
        parser.add_argument(
            "--min-price", type=int, default=0,
            help="추정가격 하한 필터 (원)",
        )
        parser.add_argument(
            "--max-price", type=int, default=MAX_PRESUME_PRICE,
            help="추정가격 상한 필터 (원, 기본 100억)",
        )
        parser.add_argument(
            "--order", type=str, default="desc",
            choices=["asc", "desc", "popular"],
            help="정렬: desc(최신순), asc(오래된순), popular(입찰자 많은순)",
        )
        parser.add_argument(
            "--min-bidders", type=int, default=0,
            help="최소 입찰자 수 필터 (기본 0)",
        )

    def handle(self, *args, **options):
        # BC-36: PID lockfile 중복 실행 방지
        lock = PidLock()
        if not lock.acquire():
            self.stderr.write(
                self.style.ERROR(
                    "이미 실행 중인 collect_bid_api_data 프로세스가 있습니다. "
                    f"(lockfile: {LOCK_FILE})"
                )
            )
            sys.exit(1)

        try:
            self._handle_inner(*args, **options)
        finally:
            lock.release()

    def _handle_inner(self, *args, **options):
        limit = options["limit"]
        daily_limit = options["daily_limit"]
        skip_a_value = options["skip_a_value"]
        skip_prelim = options["skip_prelim"]
        force = options["force"]
        min_price = options["min_price"]
        max_price = options["max_price"]
        order = options["order"]
        min_bidders = options["min_bidders"]

        # 1. 대상 공고 추출
        self.stdout.write("BidResult에서 대상 공고 추출 중...")
        targets = self._extract_targets(
            limit, force, min_price, max_price, order, min_bidders,
        )
        self.stdout.write(f"  수집 대상: {len(targets)}건")

        if not targets:
            self.stdout.write(self.style.WARNING("수집 대상 없음"))
            return

        # 2. API 수집
        api_key = get_api_key()
        stats = self._collect(
            targets, api_key, daily_limit,
            skip_a_value, skip_prelim,
        )

        # 3. 요약
        self._print_summary(stats)

    def _extract_targets(
        self, limit: int, force: bool,
        min_price: int, max_price: int,
        order: str = "desc", min_bidders: int = 0,
    ) -> list[tuple[str, str]]:
        """BidResult에서 적격심사 건설 <100억 고유 공고를 추출한다."""
        from django.db.models import Count

        qs = (
            BidResult.objects
            .filter(
                presume_price__gt=min_price,
                presume_price__lt=max_price,
                estimated_price__gt=0,
                success_lowest_rate__gt=0,
            )
            .values("bid_ntce_no", "bid_ntce_ord")
            .annotate(bidder_cnt=Count("id"))
        )

        if min_bidders > 0:
            qs = qs.filter(bidder_cnt__gte=min_bidders)

        if order == "popular":
            qs = qs.order_by("-bidder_cnt")
        elif order == "asc":
            qs = qs.order_by("bid_ntce_no")
        else:
            qs = qs.order_by("-bid_ntce_no")

        if not force:
            collected = set(
                BidApiCollectionLog.objects
                .values_list("bid_ntce_no", "bid_ntce_ord")
                .distinct()
            )
            targets = []
            for row in qs.iterator():
                key = (row["bid_ntce_no"], row["bid_ntce_ord"])
                if key not in collected:
                    targets.append(key)
                    if len(targets) >= limit:
                        break
        else:
            targets = [
                (row["bid_ntce_no"], row["bid_ntce_ord"])
                for row in qs[:limit]
            ]

        return targets

    def _collect(
        self,
        targets: list[tuple[str, str]],
        api_key: str,
        daily_limit: int,
        skip_a_value: bool,
        skip_prelim: bool,
    ) -> dict:
        """A값 + 복수예비가격 API 수집 (동기)."""
        stats = {
            "total": len(targets),
            "a_ok": 0, "a_empty": 0, "a_error": 0, "a_skip": 0,
            "p_ok": 0, "p_empty": 0, "p_error": 0, "p_skip": 0,
            "api_calls": 0,
            "abort_reason": None,
        }

        consecutive_errors = 0

        with httpx.Client(timeout=30.0) as client:
            for i, (ntce_no, ntce_ord) in enumerate(targets, 1):
                # 일일 한도 체크
                if stats["api_calls"] >= daily_limit:
                    stats["abort_reason"] = f"일일 한도 도달 ({daily_limit}건)"
                    self.stdout.write(
                        self.style.WARNING(
                            f"\n일일 한도 도달 ({daily_limit}건). "
                            f"{i - 1}/{stats['total']}건 수집 후 중단."
                        )
                    )
                    break

                # CollectionLog 생성/업데이트
                log, _ = BidApiCollectionLog.objects.update_or_create(
                    bid_ntce_no=ntce_no,
                    bid_ntce_ord=ntce_ord,
                    defaults={
                        "a_value_status": "pending",
                        "prelim_status": "pending",
                        "error_detail": "",
                    },
                )

                a_status_str = ""
                p_status_str = ""

                try:
                    # ── A값 수집 ──
                    if skip_a_value:
                        a_status_str = "skip"
                        stats["a_skip"] += 1
                    else:
                        a_result = self._collect_a_value(
                            client, api_key, ntce_no, ntce_ord, log,
                        )
                        a_status_str = a_result
                        stats[f"a_{a_result}"] += 1
                        stats["api_calls"] += 1
                        time.sleep(REQUEST_DELAY)

                    # ── 복수예비가격 수집 ──
                    if skip_prelim:
                        p_status_str = "skip"
                        stats["p_skip"] += 1
                    else:
                        p_result = self._collect_prelim(
                            client, api_key, ntce_no, ntce_ord, log,
                        )
                        p_status_str = p_result
                        stats[f"p_{p_result}"] += 1
                        stats["api_calls"] += 1
                        time.sleep(REQUEST_DELAY)

                except RateLimitError as e:
                    # BC-36: 429/한도 초과 → 즉시 중단
                    reason = str(e)
                    stats["abort_reason"] = reason
                    self.stdout.write(
                        self.style.ERROR(f"\n{reason} — 수집 즉시 중단.")
                    )
                    break

                # 진행상황
                display = f"{ntce_no}-{ntce_ord}"
                self.stdout.write(
                    f"[{i:>4}/{stats['total']}] {display:30s}: "
                    f"A={a_status_str:<8s} P={p_status_str}"
                )

                # BC-36: 연속 에러 카운트 (error만, empty/ok/skip은 정상)
                if a_status_str == "error" or p_status_str == "error":
                    consecutive_errors += 1
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        stats["abort_reason"] = (
                            f"연속 에러 {MAX_CONSECUTIVE_ERRORS}회"
                        )
                        self.stdout.write(
                            self.style.ERROR(
                                f"\n연속 에러 {MAX_CONSECUTIVE_ERRORS}회 도달. "
                                f"수집 중단."
                            )
                        )
                        break
                else:
                    consecutive_errors = 0

        return stats

    def _save_raw_json(self, directory: Path, ntce_no: str, ntce_ord: str, data: dict):
        """API 응답 JSON 원본을 파일로 저장."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{ntce_no}_{ntce_ord}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _collect_a_value(
        self,
        client: httpx.Client,
        api_key: str,
        ntce_no: str,
        ntce_ord: str,
        log: BidApiCollectionLog,
    ) -> str:
        """A값 API 수집. JSON 원본 저장 → DB 적재."""
        params = {
            "ServiceKey": api_key,
            "type": "json",
            "numOfRows": 10,
            "pageNo": 1,
            "inqryDiv": "2",
            "bidNtceNo": ntce_no,
        }
        data = call_api(
            client, BID_INFO_BASE,
            "getBidPblancListBidPrceCalclAInfo", params,
        )

        if "_error" in data:
            log.a_value_status = "error"
            log.error_detail += f"A값: {data['_error']}\n"
            log.save(update_fields=["a_value_status", "error_detail", "updated_at"])
            return "error"

        items = extract_items(data)
        if not items:
            log.a_value_status = "empty"
            log.save(update_fields=["a_value_status", "updated_at"])
            return "empty"

        # JSON 원본 저장
        actual_ord = ntce_ord or items[0].get("bidNtceOrd", "") or "000"
        self._save_raw_json(RAW_A_VALUE_DIR, ntce_no, actual_ord, data)

        # 첫 번째 아이템에서 A값 추출 → DB 적재
        item = items[0]
        model_fields = {}
        for api_field, model_field in A_VALUE_API_TO_MODEL.items():
            model_fields[model_field] = parse_api_int(item.get(api_field))

        BidApiAValue.objects.update_or_create(
            bid_ntce_no=ntce_no,
            bid_ntce_ord=actual_ord,
            defaults={
                **model_fields,
                "price_decision_method": item.get("prearngPrceDcsnMthdNm", ""),
            },
        )

        # log의 ord도 actual_ord로 맞추기 (처음 빈값이었을 때)
        if not ntce_ord and actual_ord != ntce_ord:
            log.bid_ntce_ord = actual_ord
        log.a_value_status = "ok"
        log.save(update_fields=["bid_ntce_ord", "a_value_status", "updated_at"])
        return "ok"

    def _collect_prelim(
        self,
        client: httpx.Client,
        api_key: str,
        ntce_no: str,
        ntce_ord: str,
        log: BidApiCollectionLog,
    ) -> str:
        """복수예비가격 API 수집. 결과를 DB에 저장하고 상태 문자열 반환."""
        # 차수 fallback: 있으면 그대로, 없으면 빈값 → 000
        ord_candidates = [ntce_ord] if ntce_ord else ["", "000"]
        data = {}

        for ord_try in ord_candidates:
            params = {
                "ServiceKey": api_key,
                "type": "json",
                "numOfRows": 20,
                "pageNo": 1,
                "inqryDiv": "2",
                "bidNtceNo": ntce_no,
                "bidNtceOrd": ord_try,
            }
            data = call_api(
                client, AWARD_INFO_BASE,
                "getOpengResultListInfoCnstwkPreparPcDetail", params,
            )

            if "_error" not in data:
                items = extract_items(data)
                if items:
                    actual_ord = ord_try or ntce_ord or "000"
                    self._save_raw_json(RAW_PRELIM_DIR, ntce_no, actual_ord, data)
                    self._save_prelim_prices(ntce_no, actual_ord, items)

                    if not ntce_ord and actual_ord != ntce_ord:
                        log.bid_ntce_ord = actual_ord
                    log.prelim_status = "ok"
                    log.save(
                        update_fields=[
                            "bid_ntce_ord", "prelim_status", "updated_at",
                        ]
                    )
                    return "ok"

            time.sleep(REQUEST_DELAY)

        # 모든 시도 실패
        if "_error" in data:
            log.prelim_status = "error"
            log.error_detail += f"복수예비: {data['_error']}\n"
            log.save(
                update_fields=["prelim_status", "error_detail", "updated_at"]
            )
            return "error"

        log.prelim_status = "empty"
        log.save(update_fields=["prelim_status", "updated_at"])
        return "empty"

    def _save_prelim_prices(
        self, ntce_no: str, ntce_ord: str, items: list[dict],
    ):
        """복수예비가격 아이템을 DB에 저장."""
        # 기존 데이터 삭제 후 재삽입
        BidApiPrelimPrice.objects.filter(
            bid_ntce_no=ntce_no,
            bid_ntce_ord=ntce_ord,
        ).delete()

        objs = []
        for idx, item in enumerate(items, 1):
            objs.append(BidApiPrelimPrice(
                bid_ntce_no=ntce_no,
                bid_ntce_ord=ntce_ord,
                sequence_no=idx,
                basis_planned_price=parse_api_int(item.get("bsisPlnprc")),
                is_drawn=item.get("drwtYn") == "Y",
                draw_count=parse_api_int(item.get("drwtNum")),
                planned_price=parse_api_int(item.get("plnprc")),
                base_amount=parse_api_int(item.get("bssamt")),
            ))
        BidApiPrelimPrice.objects.bulk_create(objs)

    def _print_summary(self, stats: dict):
        """수집 결과 요약 출력."""
        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write("  수집 결과 요약")
        self.stdout.write("=" * 50)
        self.stdout.write(f"대상:      {stats['total']}건")
        self.stdout.write(f"API 호출:  {stats['api_calls']}건")
        self.stdout.write("")
        self.stdout.write("[A값]")
        self.stdout.write(f"  성공:    {stats['a_ok']}건")
        self.stdout.write(f"  비대상:  {stats['a_empty']}건")
        self.stdout.write(f"  에러:    {stats['a_error']}건")
        self.stdout.write(f"  스킵:    {stats['a_skip']}건")
        self.stdout.write("")
        self.stdout.write("[복수예비가격]")
        self.stdout.write(f"  성공:    {stats['p_ok']}건")
        self.stdout.write(f"  비대상:  {stats['p_empty']}건")
        self.stdout.write(f"  에러:    {stats['p_error']}건")
        self.stdout.write(f"  스킵:    {stats['p_skip']}건")

        # BC-36: 중단 사유 표시
        abort_reason = stats.get("abort_reason")
        if abort_reason:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(f"중단 사유:  {abort_reason}")
            )

        self.stdout.write("=" * 50)

        total_ok = stats["a_ok"] + stats["p_ok"]
        total_err = stats["a_error"] + stats["p_error"]
        if total_err > 0:
            self.stdout.write(
                self.style.WARNING(f"에러 {total_err}건 발생. 로그 확인 필요.")
            )
        elif not abort_reason:
            self.stdout.write(
                self.style.SUCCESS(f"수집 완료: {total_ok}건 성공, 에러 0건")
            )
