# =============================================================================
# PaymentService Dockerfile
# =============================================================================
# Multi-stage build for optimized image size and security
# =============================================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim AS production

LABEL maintainer="ecommerce-team@example.com"
LABEL service="payment-service"
LABEL version="1.0.0"
LABEL description="PaymentService microservice for EKS with Dapr pub/sub"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    SERVICE_PORT=5004 \
    DAPR_HTTP_PORT=3500 \
    DAPR_PUBSUB_NAME=pubsub \
    SIMULATE_FAILURES=false

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=appuser:appgroup app.py .

USER appuser

EXPOSE 5004

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5004/health', timeout=5)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5004", "--workers", "2", "--threads", "4", \
     "--worker-class", "gthread", "--timeout", "120", "--access-logfile", "-", \
     "--error-logfile", "-", "--capture-output", "app:app"]
