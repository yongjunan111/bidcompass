#!/bin/sh
set -eu

LIMIT="${API_DATA_LIMIT:-1000}"
DAILY_LIMIT="${API_DAILY_LIMIT:-900}"
INTERVAL="${API_SYNC_INTERVAL_SECONDS:-86400}"

echo "[scheduler:api_data] starting: limit=${LIMIT}, daily=${DAILY_LIMIT}, interval=${INTERVAL}s"
python manage.py collect_bid_api_data --limit "${LIMIT}" --daily-limit "${DAILY_LIMIT}"

while true; do
  sleep "${INTERVAL}"
  echo "[scheduler:api_data] running collection"
  python manage.py collect_bid_api_data --limit "${LIMIT}" --daily-limit "${DAILY_LIMIT}"
done
