# Multi-stage build for Next.js frontend
# CPG2PVG-AI Frontend Dockerfile

# Stage 1: Dependencies installation
FROM node:18-alpine AS deps

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Set labels
LABEL maintainer="CPG2PVG-AI Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="cpg2pvg-ai-frontend" \
      org.label-schema.description="CPG2PVG-AI Frontend Dependencies" \
      org.label-schema.version=$VERSION

# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Stage 2: Builder stage
FROM node:18-alpine AS builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_ENVIRONMENT

# Set labels
LABEL maintainer="CPG2PVG-AI Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="cpg2pvg-ai-builder" \
      org.label-schema.description="CPG2PVG-AI Frontend Builder" \
      org.label-schema.version=$VERSION

# Install build dependencies
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY package.json package-lock.json* ./

# Copy shared constants
COPY ../shared ./shared/

# Copy source code
COPY . .

# Set environment variables for build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT \
    NODE_ENV=production

# Build the application
RUN npm run build

# Stage 3: Production stage
FROM node:18-alpine AS runner

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
ARG NODE_ENV=production

# Set labels
LABEL maintainer="CPG2PVG-AI Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="cpg2pvg-ai-frontend" \
      org.label-schema.description="CPG2PVG-AI Frontend Production" \
      org.label-schema.version=$VERSION

# Set environment variables
ENV NODE_ENV=$NODE_ENV \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Install production dependencies
RUN apk add --no-cache libc6-compat dumb-init

# Create app directory
WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Set correct permission for prerender cache
RUN mkdir .next && chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Expose port
EXPOSE 3000

# Set environment variable for port
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

# Start the application
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]