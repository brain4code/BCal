#!/bin/bash

echo "🚀 Starting BCal Calendar Booking Application..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose -f docker-compose.dev.yml down

# Build and start containers
echo "📦 Building and starting containers..."
docker-compose -f docker-compose.dev.yml up --build -d

echo "⏳ Waiting for services to start..."
echo "   This may take a few minutes on first run..."

# Wait for services to be ready
echo "🔍 Checking service health..."

# Wait for PostgreSQL
echo "   Waiting for PostgreSQL..."
until docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U bcal_user -d bcal_db > /dev/null 2>&1; do
    sleep 5
done
echo "   ✅ PostgreSQL is ready"

# Wait for Backend
echo "   Waiting for Backend API..."
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    sleep 5
done
echo "   ✅ Backend API is ready"

# Wait for Frontend
echo "   Waiting for Frontend..."
until curl -f http://localhost:3000 > /dev/null 2>&1; do
    sleep 5
done
echo "   ✅ Frontend is ready"

echo ""
echo "✅ Application is ready!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "🔐 Default Admin Credentials:"
echo "   Email: admin@bcal.com"
echo "   Password: admin123"
echo ""
echo "📝 To view logs:"
echo "   docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "🛑 To stop the application:"
echo "   docker-compose -f docker-compose.dev.yml down"
echo ""
echo "🎉 Happy booking!"
