# Multi-stage build for frontend optimization
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Install necessary build dependencies for native modules
RUN apk add --no-cache \
    libc6-compat \
    python3 \
    make \
    g++

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --no-audit

# Copy source code and public directory
COPY . .
# Ensure public directory exists in builder stage and preserve any existing content
RUN mkdir -p public

# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# Ensure public directory still exists after build
RUN mkdir -p public

# Production stage
FROM node:20-alpine AS runner

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache libc6-compat

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application from builder stage
# Create public directory and copy contents
RUN mkdir -p ./public
COPY --from=builder /app/public ./public

# Set correct permissions and copy standalone app
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Copy standalone build
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the application
CMD ["node", "server.js"]
