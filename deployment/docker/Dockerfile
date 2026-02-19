# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt pyproject.toml ./
COPY src/ ./src/
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -e .

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies required for FAISS and secure execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/src /app/src
COPY pyproject.toml ./

RUN pip install --no-cache /wheels/*

# Expose the API port
EXPOSE 8000

# Run the HANERMA FastAPI server
CMD ["uvicorn", "hanerma.server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
