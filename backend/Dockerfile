FROM python:3.12-slim-bookworm@sha256:9c47360a2a0355e2da18516d0b1c2126ec22c195d2185e97347c9d98398c5bef AS builder
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.13
COPY pyproject.toml uv.lock ./
COPY backend/src ./backend/src
RUN uv sync --frozen --no-dev --group eval --no-editable && rm -rf /root/.cache
ENV TIKTOKEN_CACHE_DIR=/app/tiktoken-cache
RUN .venv/bin/python -c "import tiktoken; tiktoken.encoding_for_model('gpt-4.1-mini-2025-04-14')"

FROM python:3.12-slim-bookworm@sha256:9c47360a2a0355e2da18516d0b1c2126ec22c195d2185e97347c9d98398c5bef
ARG BUILD_SHA
LABEL org.opencontainers.image.revision=$BUILD_SHA
WORKDIR /app
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MEDINOTE_ROOT=/app MEDINOTE_STATE_DIR=/var/lib/medinote MEDINOTE_BUILD_SHA=$BUILD_SHA TIKTOKEN_CACHE_DIR=/app/tiktoken-cache MPLCONFIGDIR=/tmp/matplotlib
RUN groupadd -g 10001 medinote && useradd -u 10001 -g 10001 -M medinote && mkdir -p /var/lib/medinote && chown 10001:10001 /var/lib/medinote
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/tiktoken-cache /app/tiktoken-cache
COPY backend/src /app/backend/src
COPY data /app/data
COPY eval /app/eval
COPY public-data /app/public-data
COPY pyproject.toml uv.lock /app/
COPY frontend/package-lock.json /app/frontend/package-lock.json
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready',timeout=3)"
CMD ["uvicorn","medinote.main:create_app","--factory","--host","0.0.0.0","--port","8000","--workers","1","--no-proxy-headers","--no-access-log"]
