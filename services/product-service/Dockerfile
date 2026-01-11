# =============================================================================
# ProductService Dockerfile
# =============================================================================
# Multi-stage build for optimized image size and security
# Base image: Python 3.11 slim for minimal footprint
#
# Build: docker build -t product-service:1.0.0 .
# Run:   docker run -p 5001:5001 product-service:1.0.0
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for isolated dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production - Minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Labels for container metadata
LABEL maintainer="ecommerce-team@example.com"
LABEL service="product-service"
LABEL version="1.0.0"
LABEL description="ProductService microservice for EKS with Dapr pub/sub"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    SERVICE_PORT=5001 \
    DAPR_HTTP_PORT=3500 \
    DAPR_PUBSUB_NAME=pubsub

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup app.py .

# Switch to non-root user
USER appuser

# Expose service port
EXPOSE 5001

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/health', timeout=5)" || exit 1

# Run application with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--threads", "4", \
     "--worker-class", "gthread", "--timeout", "120", "--access-logfile", "-", \
     "--error-logfile", "-", "--capture-output", "app:app"]
