FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 otto && chown -R otto:otto /app

# Create knowledge directory
RUN mkdir -p /app/knowledge && chown -R otto:otto /app/knowledge

USER otto

# Default command
CMD ["python", "main.py", "bot"]
