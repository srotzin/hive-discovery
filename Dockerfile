# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies into a virtual environment for clean layer caching
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim

# Non-root user for security
RUN addgroup --system hive && adduser --system --ingroup hive hive

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy source
COPY --chown=hive:hive . .

USER hive

EXPOSE 8000

# PORT is injected by Render at runtime
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
