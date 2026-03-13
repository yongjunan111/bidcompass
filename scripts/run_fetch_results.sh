#!/bin/sh
set -eu

LOOKBACK_DAYS="${SYNC_LOOKBACK_DAYS:-3}"
INTERVAL="${SYNC_INTERVAL_SECONDS:-86400}"

echo "[scheduler:results] starting: days=${LOOKBACK_DAYS}, interval=${INTERVAL}s"
python manage.py fetch_winning_bids --days "${LOOKBACK_DAYS}"
python manage.py fetch_contracts --days "${LOOKBACK_DAYS}"

while true; do
  sleep "${INTERVAL}"
  echo "[scheduler:results] running sync"
  python manage.py fetch_winning_bids --days "${LOOKBACK_DAYS}"
  python manage.py fetch_contracts --days "${LOOKBACK_DAYS}"
done
