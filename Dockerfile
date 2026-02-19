
FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy strictly pinned requirements
COPY requirements.txt .

# Install dependencies (Enterprise Optimized)
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY pyproject.toml .

# Install package
RUN pip install -e .

CMD ["hanerma"]
