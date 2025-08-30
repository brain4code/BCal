#!/bin/bash

# BCal SAAS Netlify Deployment Script
# This script deploys the frontend to Netlify and provides backend deployment options

set -e

echo "🚀 BCal SAAS Netlify Deployment"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed. Please install Node.js 16+ and try again.${NC}"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm is not installed. Please install npm and try again.${NC}"
        exit 1
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ git is not installed. Please install git and try again.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Prepare frontend for Netlify
prepare_frontend() {
    echo "📱 Preparing frontend for Netlify deployment..."
    
    cd frontend
    
    # Copy Netlify-specific package.json if it exists
    if [ -f "package.json.netlify" ]; then
        cp package.json.netlify package.json
        echo "✅ Updated package.json for Netlify"
    fi
    
    # Install dependencies
    echo "📦 Installing dependencies..."
    npm ci
    
    # Check if environment variables are set
    if [ -z "$REACT_APP_API_URL" ]; then
        echo -e "${YELLOW}⚠️  REACT_APP_API_URL not set. Using default for development.${NC}"
        export REACT_APP_API_URL="http://localhost:8000/api"
    fi
    
    # Build the frontend
    echo "🔨 Building frontend..."
    npm run build
    
    echo -e "${GREEN}✅ Frontend build completed${NC}"
    cd ..
}

# Deploy to Netlify
deploy_to_netlify() {
    echo "🌐 Deploying to Netlify..."
    
    # Check if Netlify CLI is installed
    if ! command -v netlify &> /dev/null; then
        echo "📦 Installing Netlify CLI..."
        npm install -g netlify-cli
    fi
    
    # Check if user is logged in to Netlify
    if ! netlify status &> /dev/null; then
        echo "🔐 Please log in to Netlify..."
        netlify login
    fi
    
    # Deploy to Netlify
    echo "🚀 Deploying to Netlify..."
    netlify deploy --dir=frontend/build --prod
    
    echo -e "${GREEN}✅ Frontend deployed to Netlify successfully!${NC}"
}

# Show backend deployment options
show_backend_options() {
    echo ""
    echo -e "${BLUE}🔧 Backend Deployment Options:${NC}"
    echo "================================="
    echo ""
    echo "Your frontend is now deployed on Netlify, but you still need to deploy the backend services:"
    echo ""
    echo "📊 Option 1: Railway (Recommended)"
    echo "   • Perfect for FastAPI + PostgreSQL + Redis"
    echo "   • Cost: ~$20-50/month"
    echo "   • Steps:"
    echo "     1. Install Railway CLI: npm install -g @railway/cli"
    echo "     2. Login: railway login"
    echo "     3. Deploy: railway up (in backend/ directory)"
    echo "     4. Deploy licensing server: railway up (in licensing-server/ directory)"
    echo ""
    echo "📊 Option 2: Heroku"
    echo "   • Good for Python apps"
    echo "   • Cost: ~$25-100/month"
    echo "   • Requires Heroku CLI and Git deployment"
    echo ""
    echo "📊 Option 3: DigitalOcean App Platform"
    echo "   • Docker-based deployment"
    echo "   • Cost: ~$25-75/month"
    echo "   • Upload docker-compose.saas.yml"
    echo ""
    echo "📊 Option 4: AWS/GCP"
    echo "   • Enterprise-grade scaling"
    echo "   • Cost: ~$50-500+/month"
    echo "   • Requires cloud platform expertise"
    echo ""
}

# Show environment variables needed
show_environment_setup() {
    echo -e "${YELLOW}⚙️  Environment Variables Setup:${NC}"
    echo "=================================="
    echo ""
    echo "For your backend deployment, you'll need these environment variables:"
    echo ""
    echo "🔐 Required:"
    echo "   SECRET_KEY=your-super-secret-jwt-key"
    echo "   LICENSING_API_KEY=your-licensing-api-key"
    echo "   DATABASE_URL=postgresql://user:pass@host:port/db"
    echo ""
    echo "💳 Stripe (for billing):"
    echo "   STRIPE_ENABLED=true"
    echo "   STRIPE_SECRET_KEY=sk_live_your_stripe_secret"
    echo "   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret"
    echo ""
    echo "📧 Email (recommended):"
    echo "   EMAIL_ENABLED=true"
    echo "   EMAIL_HOST=smtp.gmail.com"
    echo "   EMAIL_USERNAME=your-email@gmail.com"
    echo "   EMAIL_PASSWORD=your-app-password"
    echo ""
    echo "🌍 CORS (update with your Netlify domain):"
    echo "   ALLOWED_ORIGINS=[\"https://your-site.netlify.app\"]"
    echo ""
}

# Show post-deployment steps
show_post_deployment() {
    echo -e "${GREEN}🎉 Next Steps:${NC}"
    echo "==============="
    echo ""
    echo "1. 🔧 Deploy your backend using one of the options above"
    echo "2. 🌐 Update REACT_APP_API_URL in Netlify to point to your backend"
    echo "3. 🏷️  Configure custom domain in Netlify (optional)"
    echo "4. 📊 Set up monitoring and analytics"
    echo "5. 🔐 Configure SSL and security headers"
    echo ""
    echo "📖 For detailed instructions, see DEPLOYMENT.md"
    echo ""
}

# Main execution
main() {
    check_prerequisites
    prepare_frontend
    deploy_to_netlify
    show_backend_options
    show_environment_setup
    show_post_deployment
    
    echo -e "${GREEN}🚀 Netlify deployment completed successfully!${NC}"
    echo ""
    echo "Your BCal SAAS frontend is now live on Netlify!"
    echo "Don't forget to deploy the backend services to complete your SAAS platform."
}

# Run the script
main "$@"
