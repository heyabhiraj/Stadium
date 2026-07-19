# StadiumMind AI - Backend image (Cloud Run compatible: honours $PORT).
FROM python:3.11-slim

# libgomp1 is required by xgboost/lightgbm at runtime; curl for healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code only (not the whole context).
COPY pyproject.toml ./
COPY stadiummind ./stadiummind

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run injects $PORT (default 8080); default to 8080 for local parity.
ENV PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/api/health" || exit 1

CMD ["sh", "-c", "uvicorn stadiummind.main:app --host 0.0.0.0 --port ${PORT} --workers 2"]
