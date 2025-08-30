from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Any
import re
import secrets

from ..core.database import get_db
from ..core.tenant import (
    get_tenant_context, require_organization, require_org_admin, 
    require_system_admin, TenantContext, get_organization_user_count
)
from ..models import Organization, User, Team, Subscription, License
from ..schemas.organization import (
    OrganizationCreate, OrganizationUpdate, Organization as OrganizationSchema,
    OrganizationWithStats, SubscriptionCreate, Subscription as SubscriptionSchema
)
from ..services.billing import BillingService
from ..services.licensing import LicensingService
from ..services.user import UserService

router = APIRouter()


@router.post("/organizations", response_model=OrganizationSchema)
async def create_organization(
    organization_data: OrganizationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """Create a new organization (system admin only)"""
    
    # Check if slug is available
    existing_org = db.query(Organization).filter(
        Organization.slug == organization_data.slug
    ).first()
    
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail="Organization slug already exists"
        )
    
    # Check if custom domain is available
    if organization_data.custom_domain:
        existing_domain = db.query(Organization).filter(
            Organization.custom_domain == organization_data.custom_domain
        ).first()
        
        if existing_domain:
            raise HTTPException(
                status_code=400,
                detail="Custom domain already in use"
            )
    
    # Create organization
    organization = Organization(**organization_data.dict())
    
    # Set trial end date
    from datetime import datetime, timedelta
    organization.trial_end_date = datetime.utcnow() + timedelta(days=organization_data.trial_days)
    
    db.add(organization)
    db.commit()
    db.refresh(organization)
    
    # Create trial license in background
    background_tasks.add_task(
        create_trial_license,
        organization.id,
        organization_data.max_users,
        db
    )
    
    return organization


@router.get("/organizations", response_model=List[OrganizationWithStats])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """List all organizations (system admin only)"""
    
    query = db.query(Organization)
    
    if search:
        query = query.filter(
            Organization.name.ilike(f"%{search}%") |
            Organization.slug.ilike(f"%{search}%") |
            Organization.contact_email.ilike(f"%{search}%")
        )
    
    if is_active is not None:
        query = query.filter(Organization.is_active == is_active)
    
    organizations = query.offset(skip).limit(limit).all()
    
    # Add stats to each organization
    result = []
    for org in organizations:
        user_count = get_organization_user_count(org.id, db)
        team_count = db.query(Team).filter(Team.organization_id == org.id).count()
        
        # Get subscription and license
        subscription = db.query(Subscription).filter(
            Subscription.organization_id == org.id
        ).first()
        
        license_info = db.query(License).filter(
            License.organization_id == org.id
        ).first()
        
        org_data = OrganizationWithStats(
            **org.__dict__,
            user_count=user_count,
            team_count=team_count,
            active_subscription=subscription,
            current_license=license_info,
            usage_stats={
                "users": user_count,
                "teams": team_count,
                "max_users": license_info.max_users if license_info else 0,
                "max_teams": license_info.max_teams if license_info else 0
            }
        )
        result.append(org_data)
    
    return result


@router.get("/organizations/me", response_model=OrganizationWithStats)
async def get_my_organization(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_organization)
):
    """Get current organization details"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get stats
    user_count = get_organization_user_count(organization.id, db)
    team_count = db.query(Team).filter(Team.organization_id == organization.id).count()
    
    # Get subscription and license
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization.id
    ).first()
    
    license_info = db.query(License).filter(
        License.organization_id == organization.id
    ).first()
    
    return OrganizationWithStats(
        **organization.__dict__,
        user_count=user_count,
        team_count=team_count,
        active_subscription=subscription,
        current_license=license_info,
        usage_stats={
            "users": user_count,
            "teams": team_count,
            "max_users": license_info.max_users if license_info else 0,
            "max_teams": license_info.max_teams if license_info else 0
        }
    )


@router.put("/organizations/me", response_model=OrganizationSchema)
async def update_my_organization(
    organization_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Update current organization (org admin only)"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if custom domain is available (if being changed)
    if (organization_data.custom_domain and 
        organization_data.custom_domain != organization.custom_domain):
        
        existing_domain = db.query(Organization).filter(
            and_(
                Organization.custom_domain == organization_data.custom_domain,
                Organization.id != organization.id
            )
        ).first()
        
        if existing_domain:
            raise HTTPException(
                status_code=400,
                detail="Custom domain already in use"
            )
    
    # Update organization
    update_data = organization_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    db.commit()
    db.refresh(organization)
    
    return organization


@router.post("/organizations/me/billing/subscription")
async def create_subscription(
    payment_method_id: str,
    user_count: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Create a subscription for the organization"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if already has active subscription
    existing_subscription = db.query(Subscription).filter(
        and_(
            Subscription.organization_id == organization.id,
            Subscription.status.in_(["active", "trialing"])
        )
    ).first()
    
    if existing_subscription:
        raise HTTPException(
            status_code=400,
            detail="Organization already has an active subscription"
        )
    
    # Validate user count
    if user_count < 1 or user_count > 1000:
        raise HTTPException(
            status_code=400,
            detail="User count must be between 1 and 1000"
        )
    
    try:
        billing_service = BillingService(db)
        subscription = await billing_service.create_subscription(
            organization=organization,
            user_count=user_count,
            payment_method_id=payment_method_id,
            trial_days=14
        )
        
        return {
            "status": "success",
            "subscription_id": subscription.id,
            "message": "Subscription created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/organizations/me/billing/subscription")
async def update_subscription(
    user_count: int,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Update subscription user count"""
    
    subscription = db.query(Subscription).filter(
        and_(
            Subscription.organization_id == context.organization_id,
            Subscription.status.in_(["active", "trialing"])
        )
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="No active subscription found"
        )
    
    # Validate user count
    current_users = get_organization_user_count(context.organization_id, db)
    if user_count < current_users:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce below current user count ({current_users})"
        )
    
    try:
        billing_service = BillingService(db)
        updated_subscription = await billing_service.update_subscription_quantity(
            subscription=subscription,
            new_user_count=user_count
        )
        
        return {
            "status": "success",
            "message": "Subscription updated successfully",
            "new_user_count": updated_subscription.licensed_users
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/organizations/me/billing/portal")
async def get_billing_portal(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Get Stripe billing portal URL"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        billing_service = BillingService(db)
        portal_url = await billing_service.get_billing_portal_url(organization)
        
        return {"portal_url": portal_url}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/organizations/me/billing/preview")
async def get_billing_preview(
    user_count: int,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_organization)
):
    """Get billing preview for user count"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        billing_service = BillingService(db)
        preview = await billing_service.get_usage_based_invoice_preview(
            organization=organization,
            user_count=user_count
        )
        
        return preview
        
    except Exception as e:
        # Fallback to simple calculation
        monthly_cost = user_count * 2.99
        return {
            "user_count": user_count,
            "per_user_cost": 2.99,
            "total_cost": monthly_cost,
            "currency": "USD"
        }


@router.get("/organizations/me/license")
async def get_license_info(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_organization)
):
    """Get license information"""
    
    licensing_service = LicensingService(db)
    validation = await licensing_service.validate_license(context.organization_id)
    
    return validation


@router.post("/organizations/signup")
async def organization_signup(
    organization_data: OrganizationCreate,
    admin_email: str,
    admin_password: str,
    admin_full_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Public endpoint for organization signup"""
    
    # Validate slug format
    if not re.match(r'^[a-z0-9-]+$', organization_data.slug):
        raise HTTPException(
            status_code=400,
            detail="Slug must contain only lowercase letters, numbers, and hyphens"
        )
    
    # Check if slug is available
    existing_org = db.query(Organization).filter(
        Organization.slug == organization_data.slug
    ).first()
    
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail="Organization slug already exists"
        )
    
    # Check if admin email is available
    existing_user = db.query(User).filter(
        User.email == admin_email
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    try:
        # Create organization
        organization = Organization(**organization_data.dict())
        
        # Set trial end date
        from datetime import datetime, timedelta
        organization.trial_end_date = datetime.utcnow() + timedelta(days=14)
        
        db.add(organization)
        db.commit()
        db.refresh(organization)
        
        # Create admin user
        user_service = UserService(db)
        admin_user = await user_service.create_user(
            email=admin_email,
            password=admin_password,
            full_name=admin_full_name,
            role="org_admin",
            organization_id=organization.id
        )
        
        # Create trial license in background
        background_tasks.add_task(
            create_trial_license,
            organization.id,
            organization_data.max_users,
            db
        )
        
        return {
            "status": "success",
            "organization_id": organization.id,
            "organization_slug": organization.slug,
            "admin_user_id": admin_user.id,
            "trial_days": 14,
            "message": "Organization created successfully. Trial period started."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")


# Background tasks
async def create_trial_license(organization_id: int, max_users: int, db: Session):
    """Create trial license for new organization"""
    try:
        licensing_service = LicensingService(db)
        await licensing_service.create_license(
            organization_id=organization_id,
            max_users=max_users,
            license_type="trial"
        )
    except Exception as e:
        # Log error but don't fail organization creation
        import logging
        logging.error(f"Failed to create trial license for org {organization_id}: {str(e)}")
