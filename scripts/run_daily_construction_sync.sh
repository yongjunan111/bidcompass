#!/bin/sh
set -eu

LOOKBACK_DAYS="${SYNC_LOOKBACK_DAYS:-2}"
INTERVAL_SECONDS="${SYNC_INTERVAL_SECONDS:-86400}"
INCLUDE_API_DATA="${SYNC_INCLUDE_API_DATA:-1}"
API_DATA_LIMIT="${SYNC_API_DATA_LIMIT:-50}"

run_sync() {
  echo "[scheduler] starting construction notice sync: days=${LOOKBACK_DAYS}"
  if [ "${INCLUDE_API_DATA}" = "1" ]; then
    python manage.py sync_recent_construction_data \
      --days "${LOOKBACK_DAYS}" \
      --include-api-data \
      --api-data-limit "${API_DATA_LIMIT}"
  else
    python manage.py sync_recent_construction_data --days "${LOOKBACK_DAYS}"
  fi
  echo "[scheduler] construction notice sync finished"
}

run_sync

while true; do
  sleep "${INTERVAL_SECONDS}"
  run_sync
done
