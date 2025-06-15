#!/bin/bash

# Docker Production Deployment Script
# Usage: ./scripts/prod-deploy.sh

set -e

echo "🚀 Deploying GameChat AI to Production..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create production .env file if it doesn't exist
if [ ! -f .env.production ]; then
    echo "📋 Creating .env.production file from example..."
    cp .env.production.example .env.production
    echo "⚠️  Please edit .env.production file with your actual production settings."
    exit 1
fi

# Stop existing production services
echo "🛑 Stopping existing production services..."
docker-compose -f docker-compose.prod.yml down

# Build production images
echo "🔨 Building production Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Start production services
echo "🚀 Starting production services..."
docker-compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Production services are healthy"
else
    echo "❌ Production services are not responding"
    echo "📋 Check logs: docker-compose -f docker-compose.prod.yml logs"
    exit 1
fi

# Clean up unused images
echo "🧹 Cleaning up unused Docker images..."
docker image prune -f

echo ""
echo "🎉 Production deployment completed successfully!"
echo "🌐 Application: http://localhost"
echo "🔧 API: http://localhost/api"
echo "📚 API Docs: http://localhost/api/docs"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Update: ./scripts/prod-deploy.sh"
