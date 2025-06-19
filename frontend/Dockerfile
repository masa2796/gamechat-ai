# Multi-stage build for frontend optimization
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production --no-audit --prefer-offline

# Development dependencies for build
FROM base AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --prefer-offline

# Copy source code
COPY . .

# Build the application
ENV DOCKER_BUILD=true
ENV NODE_ENV=production
RUN npm run build:ci

# Debug: Check build output
RUN echo "=== Build completed ===" && \
    ls -la .next/ && \
    echo "=== Checking standalone directory ===" && \
    ls -la .next/standalone/ 2>/dev/null || echo "Standalone directory not found"

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy the built application
COPY --from=builder /app/public ./public

# Try to copy standalone build, fall back to regular build
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]
