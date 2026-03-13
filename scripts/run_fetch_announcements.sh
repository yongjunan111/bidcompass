#!/bin/sh
set -eu

LOOKBACK_DAYS="${SYNC_LOOKBACK_DAYS:-2}"
INTERVAL="${SYNC_INTERVAL_SECONDS:-86400}"

echo "[scheduler:announcements] starting: days=${LOOKBACK_DAYS}, interval=${INTERVAL}s"
python manage.py fetch_announcements --days "${LOOKBACK_DAYS}"

while true; do
  sleep "${INTERVAL}"
  echo "[scheduler:announcements] running sync"
  python manage.py fetch_announcements --days "${LOOKBACK_DAYS}"
done
