#!/usr/bin/env bash
set -euo pipefail

INTERVAL="${SYNC_INTERVAL_SECONDS:-86400}"
ANNOUNCE_DAYS="${SYNC_LOOKBACK_DAYS:-2}"
RESULT_DAYS="${RESULT_LOOKBACK_DAYS:-3}"
API_LIMIT="${API_DATA_LIMIT:-1000}"
API_DAILY="${API_DAILY_LIMIT:-900}"

echo "[scheduler] 마이그레이션 적용..."
python manage.py migrate --noinput || echo "[WARN] 마이그레이션 실패"

echo "[scheduler] 통합 파이프라인 시작 (주기: ${INTERVAL}s)"

while true; do
  echo ""
  echo "=============================="
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 파이프라인 실행 시작"
  echo "=============================="

  echo "[1/5] 공고 수집 (최근 ${ANNOUNCE_DAYS}일)..."
  python manage.py fetch_announcements --days "$ANNOUNCE_DAYS" || echo "[WARN] 공고 수집 실패"

  echo "[2/5] 낙찰결과 수집 (최근 ${RESULT_DAYS}일)..."
  python manage.py fetch_winning_bids --days "$RESULT_DAYS" || echo "[WARN] 낙찰결과 수집 실패"

  echo "[3/5] 계약정보 수집 (최근 ${RESULT_DAYS}일)..."
  python manage.py fetch_contracts --days "$RESULT_DAYS" || echo "[WARN] 계약정보 수집 실패"

  echo "[4/5] A값/복수예비 소급수집 (한도 ${API_DAILY}건)..."
  python manage.py collect_bid_api_data --limit "$API_LIMIT" --daily-limit "$API_DAILY" || echo "[WARN] A값 수집 실패"

  echo "[5/5] A값/기초금액 미확정 공고 재확인..."
  python manage.py retry_pending_inputs || echo "[WARN] 재확인 실패"

  echo ""
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 파이프라인 완료. ${INTERVAL}초 후 재실행."
  sleep "$INTERVAL"
done
