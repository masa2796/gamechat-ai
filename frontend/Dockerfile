### Simplified single-stage Dockerfile for MVP frontend
FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Install dependencies (production only) then build
COPY package*.json ./
RUN npm ci --no-audit --prefer-offline
COPY . .
RUN npm run build || (echo 'Next.js build failed' && exit 1)

# Use non-root user
RUN addgroup -S app && adduser -S app -G app
USER app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://127.0.0.1:3000/ || exit 1

CMD ["npm", "run", "start"]
