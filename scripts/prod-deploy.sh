#!/bin/bash

# Docker Production Deployment Script for GameChat AI
# Usage: ./scripts/prod-deploy.sh [options]
# Options:
#   --no-cache: Build without cache
#   --rollback: Rollback to previous version
#   --health-check: Only run health checks

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKEND_ENV_FILE="./backend/.env.production"
HEALTH_CHECK_TIMEOUT=300
HEALTH_CHECK_INTERVAL=10

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "🔍 Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to check environment files
check_environment_files() {
    print_status "📋 Checking environment files..."
    
    # Check main production env file
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Production environment file not found: $ENV_FILE"
        if [ -f ".env.production.template" ]; then
            print_status "Creating $ENV_FILE from template..."
            cp .env.production.template "$ENV_FILE"
            print_warning "Please edit $ENV_FILE with your actual production settings."
        else
            print_error "No template file found. Please create $ENV_FILE manually."
        fi
        exit 1
    fi
    
    # Check backend env file
    if [ ! -f "$BACKEND_ENV_FILE" ]; then
        print_warning "Backend environment file not found: $BACKEND_ENV_FILE"
        if [ -f "backend/.env.production.template" ]; then
            print_status "Creating $BACKEND_ENV_FILE from template..."
            cp backend/.env.production.template "$BACKEND_ENV_FILE"
            print_warning "Please edit $BACKEND_ENV_FILE with your actual settings."
            exit 1
        fi
    fi
    
    # Check for required API keys
    if [ -f "$BACKEND_ENV_FILE" ]; then
        if ! grep -q "OPENAI_API_KEY=.*[^dummy]" "$BACKEND_ENV_FILE" || grep -q "OPENAI_API_KEY=dummy" "$BACKEND_ENV_FILE"; then
            print_error "OPENAI_API_KEY is not properly configured in $BACKEND_ENV_FILE"
            print_status "Please set a valid OpenAI API key in the environment file."
            exit 1
        fi
        print_success "OpenAI API key configuration verified"
    fi
    
    print_success "Environment files check passed"
}

# Function to perform health check
health_check() {
    local service_name=$1
    local url=$2
    local timeout=${3:-$HEALTH_CHECK_TIMEOUT}
    
    print_status "🏥 Performing health check for $service_name..."
    
    local count=0
    local max_attempts=$((timeout / HEALTH_CHECK_INTERVAL))
    
    while [ $count -lt $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            print_success "$service_name is healthy"
            return 0
        fi
        
        print_status "Waiting for $service_name... ($((count + 1))/$max_attempts)"
        sleep $HEALTH_CHECK_INTERVAL
        count=$((count + 1))
    done
    
    print_error "$service_name health check failed after ${timeout}s"
    return 1
}

# Function to backup current deployment
backup_deployment() {
    print_status "💾 Creating backup of current deployment..."
    
    local backup_dir="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Export current containers
    docker-compose -f "$COMPOSE_FILE" config > "$backup_dir/docker-compose.yml"
    
    # Save environment files
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$backup_dir/"
    fi
    if [ -f "$BACKEND_ENV_FILE" ]; then
        cp "$BACKEND_ENV_FILE" "$backup_dir/"
    fi
    
    print_success "Backup created in $backup_dir"
    echo "$backup_dir" > .last_backup
}

# Function to rollback deployment
rollback_deployment() {
    if [ ! -f .last_backup ]; then
        print_error "No backup found for rollback"
        exit 1
    fi
    
    local backup_dir=$(cat .last_backup)
    if [ ! -d "$backup_dir" ]; then
        print_error "Backup directory not found: $backup_dir"
        exit 1
    fi
    
    print_status "🔄 Rolling back to backup: $backup_dir"
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore configuration
    cp "$backup_dir/docker-compose.yml" "$COMPOSE_FILE"
    cp "$backup_dir/.env.production" "$ENV_FILE" 2>/dev/null || true
    cp "$backup_dir/.env.production" "$BACKEND_ENV_FILE" 2>/dev/null || true
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    print_success "Rollback completed"
}

# Main deployment function
deploy() {
    local no_cache=""
    
    if [ "$1" = "--no-cache" ]; then
        no_cache="--no-cache"
        print_status "🔄 Building without cache enabled"
    fi
    
    print_status "🚀 Deploying GameChat AI to Production..."
    
    # Create backup
    backup_deployment
    
    # Stop existing services gracefully
    print_status "� Stopping existing production services..."
    docker-compose -f "$COMPOSE_FILE" down --timeout 30
    
    # Build production images
    print_status "🔨 Building production Docker images..."
    docker-compose -f "$COMPOSE_FILE" build $no_cache
    
    # Start services
    print_status "🚀 Starting production services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to initialize
    print_status "⏳ Waiting for services to initialize..."
    sleep 30
    
    # Perform health checks
    print_status "🔍 Performing health checks..."
    
    # Check Redis
    if ! health_check "Redis" "http://localhost:6379" 60; then
        print_error "Redis health check failed"
        rollback_deployment
        exit 1
    fi
    
    # Check Backend
    if ! health_check "Backend API" "http://localhost:8000/health" 120; then
        print_error "Backend health check failed"
        print_status "📋 Backend logs:"
        docker-compose -f "$COMPOSE_FILE" logs --tail=50 backend
        rollback_deployment
        exit 1
    fi
    
    # Check Frontend through Nginx
    if ! health_check "Frontend (via Nginx)" "http://localhost" 60; then
        print_warning "Frontend health check failed (this might be expected if SSL is required)"
    fi
    
    # Clean up unused images
    print_status "🧹 Cleaning up unused Docker images..."
    docker image prune -f
    
    print_success "Production deployment completed successfully!"
    
    # Display useful information
    echo ""
    echo -e "${GREEN}� GameChat AI Production Deployment Summary${NC}"
    echo "============================================"
    echo -e "${BLUE}�🌐 Application:${NC} http://localhost"
    echo -e "${BLUE}🔧 API:${NC} http://localhost:8000"
    echo -e "${BLUE}📚 API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${BLUE}🏥 Health Check:${NC} http://localhost:8000/health"
    echo ""
    echo -e "${YELLOW}📋 Useful Commands:${NC}"
    echo "  View all logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  View backend logs: docker-compose -f $COMPOSE_FILE logs -f backend"
    echo "  View frontend logs: docker-compose -f $COMPOSE_FILE logs -f frontend"
    echo "  Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "  Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo "  Update deployment: ./scripts/prod-deploy.sh"
    echo "  Rollback: ./scripts/prod-deploy.sh --rollback"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    --rollback)
        rollback_deployment
        ;;
    --health-check)
        health_check "Backend API" "http://localhost:8000/health"
        health_check "Frontend" "http://localhost"
        ;;
    --no-cache)
        check_prerequisites
        check_environment_files
        deploy --no-cache
        ;;
    *)
        check_prerequisites
        check_environment_files
        deploy
        ;;
esac
