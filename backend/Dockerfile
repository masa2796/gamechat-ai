# Multi-stage build for backend optimization
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy application code and configuration
COPY backend/app/ ./app/
COPY backend/gunicorn.conf.py ./
COPY requirements.txt .

# Create data directory for cache/temporary files
RUN mkdir -p ./data /tmp/gamechat-data && \
    chmod 755 /tmp/gamechat-data && \
    chown app:app /tmp/gamechat-data

# Create minimal placeholder data files for CI/CD environments
# These will be replaced by GCS data in production
RUN echo '[{"id":"placeholder","title":"Placeholder","content":"This is a placeholder data file for CI/CD builds","category":"system","created_at":"2025-06-20T00:00:00Z"}]' > ./data/data.json && \
    echo '[{"id":"placeholder","title":"Placeholder","content":"This is a placeholder data file for CI/CD builds","category":"system","created_at":"2025-06-20T00:00:00Z"}]' > ./data/convert_data.json && \
    echo '[]' > ./data/embedding_list.jsonl && \
    echo '[]' > ./data/query_data.json

# Change ownership of app directory to ensure proper permissions
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Set PATH to include user's local bin
ENV PATH=/home/app/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
