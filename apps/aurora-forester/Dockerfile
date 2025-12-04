# Aurora Forester - Docker Image
# Personal assistant meta-agent for Graydon

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 aurora && chown -R aurora:aurora /app
USER aurora

# Default command: run Discord bot
CMD ["python", "main.py", "bot"]
