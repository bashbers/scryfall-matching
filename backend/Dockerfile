FROM python:3.14.6-alpine3.24 AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apk add --no-cache build-base \
    && pip install --no-cache-dir uv==0.12.1

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

FROM python:3.14.6-alpine3.24

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_PATH=/app/data

RUN apk upgrade --no-cache \
    && addgroup -S app \
    && adduser -S -G app -h /app app \
    && mkdir /app/data \
    && chown app:app /app/data

COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app src ./src

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)"

CMD ["uvicorn", "scryfall_matching.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
