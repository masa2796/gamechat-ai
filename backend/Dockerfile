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

# Create data directory and copy files if they exist
# This handles the case where data/ is in .gitignore but may exist locally
RUN mkdir -p ./data

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
