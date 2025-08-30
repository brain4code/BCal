# BCal SAAS Platform

A complete Software-as-a-Service (SAAS) calendar booking platform with multi-tenancy, licensing, and billing integration.

## 🌟 SAAS Features

### 💰 **Pricing Model**
- **$2.99 per user per month**
- 14-day free trial for all new organizations
- Automatic billing with Stripe integration
- Usage-based scaling

### 🏢 **Multi-Tenancy**
- Complete organization isolation
- Subdomain support (e.g., `company.bcal.com`)
- Custom domain support
- Per-tenant branding and customization

### 🎨 **White Labeling**
- Custom logos and favicons
- Configurable color schemes
- Custom CSS support
- Branded email notifications
- Custom domain names

### 🔐 **Licensing & Limits**
- Real-time license validation
- Automatic usage tracking
- Configurable user limits
- Feature-based access control
- Separate licensing server

### 📊 **SAAS Admin Portal**
- Organization management
- Subscription monitoring
- Revenue analytics
- Usage statistics
- License management

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Stripe account (for billing)
- Email service (Gmail/SMTP)
- Domain name (for production)

### 1. Clone and Setup
```bash
git clone <your-repo>
cd BCal
cp env.saas.example .env.saas
```

### 2. Configure Environment
Edit `.env.saas` with your settings:

```bash
# Required Settings
POSTGRES_PASSWORD=your-secure-password
SECRET_KEY=your-jwt-secret-key
LICENSING_API_KEY=your-licensing-api-key

# Stripe Configuration
STRIPE_ENABLED=true
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Email Configuration
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### 3. Start the Platform
```bash
./start-saas.sh
```

### 4. Access the Platform
- **Main Application**: http://localhost
- **API Documentation**: http://localhost/api/docs
- **System Admin**: admin@bcal.com / admin123

## 🏗️ Architecture

### Services
1. **Main Application** (FastAPI + React)
   - Multi-tenant API endpoints
   - Organization management
   - User authentication and authorization
   - Booking system with tenant isolation

2. **Licensing Server** (Separate FastAPI service)
   - License generation and validation
   - Usage tracking and enforcement
   - Billing integration
   - Feature access control

3. **Database Services**
   - PostgreSQL for main application
   - Separate PostgreSQL for licensing
   - Redis for caching and sessions

4. **Nginx Reverse Proxy**
   - Tenant routing by subdomain/domain
   - SSL termination
   - Static file serving
   - Rate limiting

### Multi-Tenancy Implementation

#### Tenant Identification
```
Subdomain:     company.bcal.com → organization_slug: "company"
Custom Domain: booking.company.com → custom_domain: "booking.company.com"
Path-based:    bcal.com/org/company → organization_slug: "company"
```

#### Data Isolation
- All tables have `organization_id` foreign keys
- Middleware automatically filters queries by tenant
- Cross-tenant access strictly prevented
- System admins can access all tenants

#### API Tenant Context
```python
# Automatic tenant injection
@router.get("/bookings")
async def get_bookings(
    context: TenantContext = Depends(require_organization)
):
    # context.organization_id automatically set
    # Queries automatically filtered by tenant
```

## 💳 Billing Integration

### Stripe Setup
1. Create Stripe account
2. Get API keys (test/live)
3. Configure webhook endpoint: `/api/webhooks/stripe`
4. Set webhook secret in environment

### Subscription Flow
1. Organization signs up (14-day trial)
2. Trial period allows full access
3. After trial, requires payment method
4. Automatic monthly billing at $2.99 per user
5. Usage-based scaling

### Webhook Events
- `invoice.payment_succeeded` → Activate subscription
- `invoice.payment_failed` → Suspend access
- `customer.subscription.updated` → Update limits
- `customer.subscription.deleted` → Cancel subscription

## 🔐 Licensing System

### License Types
- **Trial**: 14 days, limited features
- **Standard**: Full features, $2.99/user/month
- **Enterprise**: Custom features and pricing

### License Validation
```python
# Check license before feature access
@require_feature("advanced_analytics")
async def get_analytics():
    # Feature only available if licensed
```

### Usage Tracking
- Real-time user count monitoring
- Monthly booking limits
- API usage tracking
- Automatic license enforcement

## 🎨 White Labeling

### Customization Options
- **Visual Branding**
  - Custom logo and favicon
  - Color scheme (primary, secondary, accent)
  - Custom CSS injection
  
- **Domain Branding**
  - Custom domain names
  - Subdomain allocation
  - SSL certificate management
  
- **Communication Branding**
  - Custom email templates
  - Branded notifications
  - Custom "from" addresses

### API Endpoints
```bash
# Get branding configuration
GET /api/branding

# Update branding
PUT /api/branding

# Upload logo
POST /api/branding/logo

# Apply theme
POST /api/branding/themes/professional
```

## 📊 Admin Portal

### System Admin Features
- View all organizations
- Monitor subscriptions and revenue
- Manage licenses
- Usage analytics
- System maintenance

### Organization Admin Features
- Manage organization settings
- Configure branding
- Handle billing and subscriptions
- Monitor usage and limits
- Invite team members

### Dashboard Metrics
- Total revenue and growth
- Organization statistics
- User activity and engagement
- License utilization
- System performance

## 🔧 Configuration

### Environment Variables
```bash
# Multi-tenancy
ENABLE_MULTI_TENANCY=true
DEFAULT_ORGANIZATION_NAME=Default Organization
TRIAL_DAYS=14
MAX_ORGANIZATIONS=1000

# Licensing
LICENSING_SERVER_URL=http://licensing-server:8001
LICENSING_API_KEY=your-api-key

# Billing
STRIPE_ENABLED=true
STRIPE_SECRET_KEY=sk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Features
EMAIL_ENABLED=true
VIDEO_CONFERENCING_ENABLED=true
CUSTOM_BRANDING_ENABLED=true
```

### Database Configuration
- Automatic migrations on startup
- Separate databases for isolation
- Connection pooling and optimization
- Backup and restore capabilities

## 🚀 Deployment

### Development
```bash
# Start development environment
./start-saas.sh
```

### Production
1. **Domain Setup**
   ```bash
   # Main domain
   bcal.com → Load Balancer → BCal Services
   
   # Wildcard subdomain
   *.bcal.com → Load Balancer → BCal Services
   
   # Custom domains
   booking.company.com → CNAME → bcal.com
   ```

2. **SSL Configuration**
   ```bash
   # Update nginx.saas.conf
   ssl_certificate /etc/nginx/ssl/cert.pem;
   ssl_certificate_key /etc/nginx/ssl/key.pem;
   ```

3. **Environment Setup**
   ```bash
   # Production environment
   cp .env.saas .env.production
   # Update with production values
   ```

4. **Monitoring Setup**
   - Health check endpoints
   - Log aggregation
   - Performance monitoring
   - Error tracking

## 📈 Scaling

### Horizontal Scaling
- Load balancer configuration
- Database read replicas
- Redis clustering
- CDN for static assets

### Performance Optimization
- Database indexing
- Query optimization
- Caching strategies
- Background job processing

### Monitoring
- Application metrics
- Database performance
- Resource utilization
- User activity tracking

## 🔒 Security

### Tenant Isolation
- Database-level isolation
- API access controls
- File storage separation
- Cross-tenant protection

### Authentication & Authorization
- JWT token-based auth
- Role-based access control
- Multi-factor authentication
- SSO integration support

### Data Protection
- Encryption at rest
- Secure communication
- PII data handling
- GDPR compliance

## 🧪 Testing

### Development Testing
```bash
# Run API tests
docker-compose -f docker-compose.saas.yml exec backend python -m pytest

# Run Karate tests
cd tests/karate
mvn test
```

### Load Testing
```bash
# Simulate multiple tenants
artillery run load-test-config.yml
```

## 🤝 Support

### Documentation
- API documentation: `/api/docs`
- User guides and tutorials
- Admin portal documentation
- Integration guides

### Monitoring
- Health check endpoints
- System status dashboard
- Error reporting
- Performance metrics

## 📝 License

MIT License - See LICENSE file for details.

## 🙏 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

---

**BCal SAAS Platform** - Complete calendar booking solution with enterprise-grade multi-tenancy, billing, and white-labeling capabilities.
