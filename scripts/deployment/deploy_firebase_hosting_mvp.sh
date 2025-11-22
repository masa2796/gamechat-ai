#!/usr/bin/env bash
set -euo pipefail

# MVP Firebase Hosting deploy script.
# Prerequisites: npm i -g firebase-tools && firebase login && firebase use <project>
# Assumes frontend mvp static export (next export => frontend/out)

FRONTEND_DIR=frontend
BUILD_CMD=${BUILD_CMD:-"npm run mvp:build"}
PROJECT_ID=${PROJECT_ID:-your-firebase-project}
CHANNEL=${CHANNEL:-live}

pushd "$FRONTEND_DIR" >/dev/null

if [[ ! -d node_modules ]]; then
  echo "Installing dependencies..." >&2
  npm ci || npm install
fi

echo "Building (MVP export)..." >&2
# Ensure env var for build
export NEXT_PUBLIC_MVP_MODE=true
$BUILD_CMD

if [[ ! -d out ]]; then
  echo "ERROR: out directory not produced. Check next.config.js output settings." >&2
  exit 1
fi

popd >/dev/null

echo "Deploying to Firebase Hosting (project=$PROJECT_ID channel=$CHANNEL)" >&2
firebase deploy --only hosting --project "$PROJECT_ID"

echo "Deployment finished." >&2
