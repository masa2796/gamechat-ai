### Simplified single-stage Dockerfile for MVP backend
# - Multi-stage, build tooling, gunicorn removed
# - Runs uvicorn directly
# - Minimal optional data copy guarded

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Layer cache: install deps first
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# App source
COPY backend/app ./app

# Optional data (ignore if absent)
RUN mkdir -p data && \
    if [ -f data/convert_data.json ]; then cp data/convert_data.json data/; fi || true && \
    if [ -f data/data.json ]; then cp data/data.json data/; fi || true

# Temp directory used by StorageService
RUN mkdir -p /tmp/gamechat-data && chown -R app:app /app /tmp/gamechat-data

USER app

EXPOSE 8000

# Lightweight healthcheck using python stdlib
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request,sys;\ntry:\n r=urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2); sys.exit(0 if r.status==200 else 1)\nexcept Exception: sys.exit(1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
