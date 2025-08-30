#!/bin/bash

# BCal SAAS Deployment Script
# This script sets up and starts the BCal SAAS platform with multi-tenancy and licensing

set -e

echo "🚀 Starting BCal SAAS Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env.saas exists
if [ ! -f .env.saas ]; then
    echo -e "${YELLOW}⚠️  .env.saas file not found. Creating from template...${NC}"
    cp env.saas.example .env.saas
    echo -e "${RED}❌ Please edit .env.saas with your configuration before continuing!${NC}"
    echo "Required settings:"
    echo "  - POSTGRES_PASSWORD"
    echo "  - SECRET_KEY"
    echo "  - STRIPE_SECRET_KEY (for billing)"
    echo "  - EMAIL configuration (recommended)"
    exit 1
fi

# Load environment variables
set -a
source .env.saas
set +a

# Validate required environment variables
validate_env() {
    local required_vars=(
        "POSTGRES_PASSWORD"
        "SECRET_KEY"
        "LICENSING_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo -e "${RED}❌ Required environment variable $var is not set!${NC}"
            exit 1
        fi
    done
    
    if [ "$STRIPE_ENABLED" = "true" ] && [ -z "$STRIPE_SECRET_KEY" ]; then
        echo -e "${RED}❌ Stripe is enabled but STRIPE_SECRET_KEY is not set!${NC}"
        exit 1
    fi
}

echo "🔍 Validating environment configuration..."
validate_env
echo -e "${GREEN}✅ Environment validation passed${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed. Please install it and try again.${NC}"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads/branding
mkdir -p ssl
mkdir -p backups

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.saas.yml down --remove-orphans

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.saas.yml pull

# Build custom images
echo "🔨 Building application images..."
docker-compose -f docker-compose.saas.yml build

# Start services
echo "🎯 Starting BCal SAAS services..."
docker-compose -f docker-compose.saas.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
check_service_health() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is healthy${NC}"
            return 0
        fi
        echo "⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start properly${NC}"
    return 1
}

echo "🏥 Checking service health..."
check_service_health "Licensing Server" "http://localhost/licensing/health"
check_service_health "Backend API" "http://localhost/api/health"
check_service_health "Frontend" "http://localhost/"

# Run database migrations
echo "📊 Running database migrations..."
docker-compose -f docker-compose.saas.yml exec backend alembic upgrade head

# Create default system admin user
echo "👤 Creating system admin user..."
docker-compose -f docker-compose.saas.yml exec backend python -c "
import asyncio
from app.core.database import SessionLocal
from app.services.user import UserService

async def create_admin():
    db = SessionLocal()
    user_service = UserService(db)
    try:
        admin = await user_service.create_system_admin(
            email='admin@bcal.com',
            password='admin123',
            full_name='System Administrator'
        )
        print(f'System admin created: {admin.email}')
    except Exception as e:
        print(f'Admin already exists or error: {e}')
    finally:
        db.close()

asyncio.run(create_admin())
"

# Display success information
echo ""
echo -e "${GREEN}🎉 BCal SAAS Platform is now running!${NC}"
echo ""
echo "📱 Access URLs:"
echo "  🌐 Main Application: http://localhost"
echo "  📊 API Documentation: http://localhost/api/docs"
echo "  🔑 System Admin Login:"
echo "    Email: admin@bcal.com"
echo "    Password: admin123"
echo ""
echo "🏢 Multi-tenancy Support:"
echo "  📝 Organization Signup: http://localhost/signup"
echo "  🔗 Subdomain Access: http://[org-slug].localhost"
echo "  🌍 Custom Domain: Configure DNS to point to your server"
echo ""
echo "💰 SAAS Features:"
echo "  💳 Stripe Billing: $([ "$STRIPE_ENABLED" = "true" ] && echo "✅ Enabled" || echo "❌ Disabled")"
echo "  📧 Email Notifications: $([ "$EMAIL_ENABLED" = "true" ] && echo "✅ Enabled" || echo "❌ Disabled")"
echo "  🏷️ White Labeling: ✅ Available"
echo "  📊 Usage Tracking: ✅ Active"
echo ""
echo "🔧 Management:"
echo "  📊 View logs: docker-compose -f docker-compose.saas.yml logs -f"
echo "  🛑 Stop services: docker-compose -f docker-compose.saas.yml down"
echo "  🔄 Restart: ./start-saas.sh"
echo ""

# Show container status
echo "📋 Container Status:"
docker-compose -f docker-compose.saas.yml ps

# Show important security warnings
echo ""
echo -e "${YELLOW}⚠️  SECURITY REMINDERS:${NC}"
echo "1. Change default admin password immediately"
echo "2. Configure SSL certificates for production"
echo "3. Set strong database passwords"
echo "4. Configure proper firewall rules"
echo "5. Enable backups for production data"
echo ""

if [ "$STRIPE_ENABLED" = "true" ]; then
    echo -e "${BLUE}💡 Stripe Integration:${NC}"
    echo "• Test mode: Use test card 4242 4242 4242 4242"
    echo "• Live mode: Configure webhook endpoints in Stripe dashboard"
    echo "• Webhook URL: https://yourdomain.com/api/webhooks/stripe"
    echo ""
fi

echo -e "${GREEN}🚀 BCal SAAS Platform is ready to use!${NC}"
