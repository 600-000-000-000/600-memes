# Stage 1: Build SolidJS frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends curl ffmpeg && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

COPY backend/ .
COPY nostr.json members.json /app/
RUN curl -sf --max-time 10 https://600.wtf/.well-known/nostr.json -o /app/nostr.json || echo "Using local nostr.json" && \
    curl -sf --max-time 10 https://600.wtf/members.json -o /app/members.json   || echo "Using local members.json"
COPY --from=frontend-builder /build/dist /app/static

RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
