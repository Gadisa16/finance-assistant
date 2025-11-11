#!/usr/bin/env sh
set -eu

# Simple wait for DB by probing Alembic metadata (retries)
echo "[startup] Waiting for database to be ready..."
retries=30
sleep_seconds=2

i=1
while [ $i -le $retries ]; do
  if alembic current >/dev/null 2>&1; then
    echo "[startup] Database reachable."
    break
  fi
  echo "[startup] DB not ready yet ($i/$retries). Sleeping ${sleep_seconds}s..."
  sleep $sleep_seconds
  i=$((i+1))
done

if [ $i -gt $retries ]; then
  echo "[startup] ERROR: Database not reachable after $((retries*sleep_seconds))s" >&2
  exit 1
fi

echo "[startup] Applying migrations..."
alembic upgrade head

echo "[startup] Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
