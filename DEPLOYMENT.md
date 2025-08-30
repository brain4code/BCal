# BCal SAAS Deployment Guide

This guide covers deploying BCal SAAS across multiple platforms for optimal performance and cost-effectiveness.

## 🏗️ **Architecture Overview**

BCal SAAS requires multiple services:
- **Frontend (React)**: Static site deployment
- **Backend API (FastAPI)**: Server deployment
- **Licensing Server**: Separate server deployment
- **PostgreSQL Databases**: Managed database hosting
- **Redis Cache**: Managed cache hosting
- **File Storage**: CDN/Object storage

## 🚀 **Option 1: Netlify + Railway (Recommended)**

### **Frontend on Netlify**
✅ **Perfect for**: React frontend, CDN, custom domains
💰 **Cost**: Free tier available, ~$19/month for pro features

### **Backend on Railway**
✅ **Perfect for**: FastAPI apps, PostgreSQL, Redis, auto-scaling
💰 **Cost**: Pay-per-use, ~$20-50/month for small to medium apps

---

## 📱 **Frontend Deployment (Netlify)**

### Step 1: Prepare Frontend
```bash
cd frontend
cp package.json.netlify package.json
```

### Step 2: Connect to Netlify
1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Netlify deployment"
   git push origin main
   ```

2. **Connect Repository**:
   - Go to [Netlify Dashboard](https://app.netlify.com)
   - Click "New site from Git"
   - Connect your GitHub repository
   - Select the BCal repository

### Step 3: Configure Build Settings
```yaml
Build command: cd frontend && npm ci && npm run build
Publish directory: frontend/build
```

### Step 4: Set Environment Variables
In Netlify dashboard → Site settings → Environment variables:
```bash
REACT_APP_API_URL=https://your-backend.railway.app/api
REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
REACT_APP_ENABLE_MULTI_TENANCY=true
NODE_VERSION=18
```

### Step 5: Configure Custom Domain
1. **Add Domain**: Site settings → Domain management
2. **DNS Configuration**:
   ```
   @ → your-site.netlify.app (or Netlify Load Balancer IP)
   www → your-site.netlify.app
   *.yourdomain.com → your-site.netlify.app (for subdomains)
   ```

---

## 🔧 **Backend Deployment (Railway)**

### Step 1: Prepare Backend for Railway
Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 2: Deploy to Railway
1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Initialize**:
   ```bash
   railway login
   railway init
   ```

3. **Add Services**:
   ```bash
   # Add PostgreSQL
   railway add postgresql
   
   # Add Redis
   railway add redis
   
   # Deploy main backend
   railway up
   ```

### Step 3: Configure Environment Variables
In Railway dashboard:
```bash
# Database
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Security
SECRET_KEY=your-super-secret-jwt-key
LICENSING_API_KEY=your-licensing-api-key

# Stripe
STRIPE_ENABLED=true
STRIPE_SECRET_KEY=sk_live_your_stripe_secret
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Email
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# CORS
ALLOWED_ORIGINS=["https://yourdomain.com","https://*.yourdomain.com"]
```

### Step 4: Deploy Licensing Server
Create separate Railway service:
```bash
# In licensing-server directory
railway init
railway up
```

Set environment variables:
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
LICENSE_SERVER_SECRET=your-licensing-secret
LICENSING_API_KEY=your-licensing-api-key
```

---

## 🌐 **Option 2: Vercel + PlanetScale**

### **Frontend on Vercel**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod
```

### **Backend on Railway/Heroku**
Same as Option 1 backend deployment

### **Database on PlanetScale**
- MySQL-compatible serverless database
- Excellent for global scaling
- Built-in branching and migrations

---

## 🏢 **Option 3: Full AWS Deployment**

### **Frontend**
- **S3 + CloudFront**: Static hosting with global CDN
- **Route 53**: DNS management for custom domains

### **Backend**
- **ECS Fargate**: Containerized backend services
- **Application Load Balancer**: Multi-tenant routing
- **RDS PostgreSQL**: Managed database
- **ElastiCache Redis**: Managed cache

### **Cost Estimation**
- Small deployment: ~$50-100/month
- Medium deployment: ~$200-500/month
- Enterprise: $500+/month

---

## 📊 **Recommended Setup by Scale**

### **Startup (0-100 users)**
- **Frontend**: Netlify (Free)
- **Backend**: Railway ($20-30/month)
- **Database**: Railway PostgreSQL (included)
- **Total**: ~$20-30/month

### **Growing Business (100-1000 users)**
- **Frontend**: Netlify Pro ($19/month)
- **Backend**: Railway Pro ($50-100/month)
- **Database**: Dedicated PostgreSQL ($20-50/month)
- **Total**: ~$90-170/month

### **Enterprise (1000+ users)**
- **Frontend**: Netlify Business ($99/month)
- **Backend**: AWS/GCP ($200-500/month)
- **Database**: Managed PostgreSQL ($100-300/month)
- **Total**: ~$400-900/month

---

## 🔐 **Security Configuration**

### SSL Certificates
```bash
# Netlify - Automatic Let's Encrypt
# Railway - Automatic SSL

# For custom domains, configure:
# 1. DNS records
# 2. SSL certificate verification
# 3. HTTPS redirects
```

### Environment Secrets
```bash
# Never commit to git:
.env
.env.local
.env.production

# Use platform secret management:
# - Netlify: Environment variables
# - Railway: Environment variables
# - AWS: Systems Manager Parameter Store
```

---

## 📈 **Monitoring & Analytics**

### Application Monitoring
```bash
# Add to backend
SENTRY_DSN=your_sentry_dsn

# Add to frontend
REACT_APP_SENTRY_DSN=your_frontend_sentry_dsn
```

### Performance Monitoring
- **Netlify Analytics**: Built-in frontend analytics
- **Railway Metrics**: Backend performance monitoring
- **Custom Dashboard**: Grafana + Prometheus

---

## 🚀 **Deployment Commands**

### Quick Deploy Script
Create `deploy.sh`:
```bash
#!/bin/bash
echo "🚀 Deploying BCal SAAS..."

# Deploy frontend to Netlify
echo "📱 Deploying frontend..."
cd frontend
npm run build
netlify deploy --prod --dir=build

# Deploy backend to Railway
echo "🔧 Deploying backend..."
cd ../backend
railway up

# Deploy licensing server
echo "🔐 Deploying licensing server..."
cd ../licensing-server
railway up

echo "✅ Deployment complete!"
```

### Automated CI/CD
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy BCal SAAS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Netlify
        uses: netlify/actions/cli@master
        with:
          args: deploy --dir=frontend/build --prod
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
      
      - name: Deploy to Railway
        uses: railway-app/railway@v1
        with:
          token: ${{ secrets.RAILWAY_TOKEN }}
```

---

## 🎯 **Next Steps**

1. **Choose deployment option** based on your needs and budget
2. **Set up monitoring** and error tracking
3. **Configure backup strategy** for databases
4. **Set up CI/CD pipeline** for automated deployments
5. **Configure custom domains** and SSL certificates
6. **Test multi-tenant routing** with subdomains
7. **Set up Stripe webhooks** for production billing

---

## 🆘 **Troubleshooting**

### Common Issues
1. **CORS errors**: Update `ALLOWED_ORIGINS` in backend
2. **Stripe webhooks**: Configure correct endpoint URLs
3. **Database connections**: Check connection strings
4. **Environment variables**: Verify all required vars are set

### Support Resources
- [Netlify Documentation](https://docs.netlify.com)
- [Railway Documentation](https://docs.railway.app)
- [BCal SAAS GitHub Issues](your-repo-issues-url)

The deployment is now ready for production use with proper scaling, security, and monitoring capabilities!
