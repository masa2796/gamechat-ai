#!/usr/bin/env bash
set -euo pipefail

# MVP Cloud Run deploy script (idempotent-ish). Adjust PROJECT_ID & SERVICE before running.
# Requirements: gcloud auth login && gcloud config set project <PROJECT_ID>

PROJECT_ID=${PROJECT_ID:-your-gcp-project}
REGION=${REGION:-asia-northeast1}
SERVICE=${SERVICE:-gamechat-ai-backend}
IMAGE=gcr.io/$PROJECT_ID/$SERVICE:$(date +%Y%m%d%H%M%S)
PORT=8000
PLATFORM=managed

# Load env file (expects key=value lines)
ENV_FILE=${ENV_FILE:-backend/.env.prod}
if [[ -f "$ENV_FILE" ]]; then
  echo "Loading env vars from $ENV_FILE" >&2
  # shellcheck disable=SC2046
  export $(grep -v '^#' "$ENV_FILE" | xargs -d'\n') || true
else
  echo "WARNING: Env file $ENV_FILE not found. Proceeding with current environment." >&2
fi

# Normalize LOG_LEVEL -> BACKEND_LOG_LEVEL for compatibility
if [[ -z "${BACKEND_LOG_LEVEL:-}" && -n "${LOG_LEVEL:-}" ]]; then
  echo "[hint] Mapping LOG_LEVEL -> BACKEND_LOG_LEVEL ($LOG_LEVEL)" >&2
  export BACKEND_LOG_LEVEL="$LOG_LEVEL"
fi

# Build image
echo "[1/3] Building image $IMAGE" >&2
docker build -f backend/Dockerfile -t "$IMAGE" .

echo "[2/3] Pushing image" >&2
docker push "$IMAGE"

# Assemble --set-env-vars list (only whitelisted keys)
# Prefer BACKEND_LOG_LEVEL over LOG_LEVEL. Keep LOG_LEVEL for legacy until fully removed.
ENV_KEYS=(
  BACKEND_ENVIRONMENT
  BACKEND_LOG_LEVEL
  BACKEND_OPENAI_API_KEY
  UPSTASH_VECTOR_REST_URL
  UPSTASH_VECTOR_REST_TOKEN
  UPSTASH_VECTOR_INDEX_NAME
  LOG_LEVEL
  VECTOR_TOP_K
  VECTOR_TIMEOUT_SECONDS
  LLM_TIMEOUT_SECONDS
  CORS_ORIGINS
)
ENV_ARGS=()
for k in "${ENV_KEYS[@]}"; do
  if [[ -n "${!k:-}" ]]; then
    ENV_ARGS+=("${k}=${!k}")
  fi
done

ENV_ARG_LIST=$(IFS=','; echo "${ENV_ARGS[*]}")

echo "[3/3] Deploying to Cloud Run service=$SERVICE region=$REGION" >&2

gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform "$PLATFORM" \
  --allow-unauthenticated \
  --port "$PORT" \
  --cpu 1 \
  --memory 512Mi \
  --max-instances 3 \
  --set-env-vars "${ENV_ARG_LIST}" \
  --ingress all

echo "Done. Service URL:" >&2
gcloud run services describe "$SERVICE" --region "$REGION" --format 'value(status.url)'
