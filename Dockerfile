FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

WORKDIR /app
COPY frontend /app/frontend
RUN cd frontend && npm run build

FROM python:3.10-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# App code first (needed for pip install .)
COPY . .
COPY --from=frontend-builder /app/static/frontend /opt/frontend-dist

# Python deps
RUN pip install --no-cache-dir .

# Collect static files
RUN mkdir -p /app/static/frontend && \
    cp -r /opt/frontend-dist/. /app/static/frontend/ && \
    python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8010

CMD ["sh", "-c", "mkdir -p /app/static/frontend && cp -r /opt/frontend-dist/. /app/static/frontend/ && python manage.py collectstatic --noinput 2>/dev/null || true && python manage.py runserver 0.0.0.0:8010"]
