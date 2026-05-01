# ──────────────────────────────────────────────
# Stage 1 — builder
# Installs dependencies into an isolated prefix so
# the runtime stage receives only what it needs.
# ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /install

# System deps required by psycopg2-binary (libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/packages -r requirements.txt


# ──────────────────────────────────────────────
# Stage 2 — runtime
# Lean image with only the application and its
# installed packages. Runs as a non-root user.
# ──────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# System runtime lib for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install/packages /usr/local

WORKDIR /app

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Application source
COPY . .

# Model artifacts directory — will be mounted as a volume in compose
RUN mkdir -p models && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Runs migrations then starts uvicorn.
# Using sh -c so environment variables are expanded at runtime.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
