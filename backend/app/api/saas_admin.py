from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.tenant import require_system_admin, TenantContext
from ..models import Organization, User, Team, Subscription, License, UsageLog, Booking
from ..schemas.organization import (
    OrganizationWithStats, Subscription as SubscriptionSchema,
    License as LicenseSchema, UsageLog as UsageLogSchema
)
from ..services.billing import BillingService
from ..services.licensing import LicensingService
from ..services.usage_tracking import UsageTrackingService

router = APIRouter()


@router.get("/saas/dashboard")
async def get_saas_dashboard(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """Get SAAS dashboard overview statistics"""
    
    # Total counts
    total_organizations = db.query(Organization).count()
    active_organizations = db.query(Organization).filter(Organization.is_active == True).count()
    total_users = db.query(User).count()
    total_teams = db.query(Team).count()
    total_bookings = db.query(Booking).count()
    
    # Active subscriptions
    active_subscriptions = db.query(Subscription).filter(
        Subscription.status.in_(["active", "trialing"])
    ).count()
    
    # Revenue calculation (active subscriptions only)
    revenue_query = db.query(
        func.sum(Subscription.licensed_users * Subscription.price_per_user)
    ).filter(
        Subscription.status == "active"
    ).scalar()
    monthly_revenue = float(revenue_query or 0)
    
    # Growth metrics (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    new_organizations = db.query(Organization).filter(
        Organization.created_at >= thirty_days_ago
    ).count()
    
    new_users = db.query(User).filter(
        User.created_at >= thirty_days_ago
    ).count()
    
    new_bookings = db.query(Booking).filter(
        Booking.created_at >= thirty_days_ago
    ).count()
    
    # Trial vs paid organizations
    trial_orgs = db.query(Organization).filter(
        and_(
            Organization.is_active == True,
            Organization.trial_end_date > datetime.utcnow()
        )
    ).count()
    
    paid_orgs = active_subscriptions
    
    # Top organizations by usage
    top_orgs = db.query(
        Organization.name,
        Organization.slug,
        func.count(User.id).label('user_count'),
        func.count(Team.id).label('team_count')
    ).outerjoin(User).outerjoin(Team).group_by(
        Organization.id, Organization.name, Organization.slug
    ).order_by(desc('user_count')).limit(10).all()
    
    return {
        "overview": {
            "total_organizations": total_organizations,
            "active_organizations": active_organizations,
            "total_users": total_users,
            "total_teams": total_teams,
            "total_bookings": total_bookings,
            "active_subscriptions": active_subscriptions,
            "monthly_revenue": monthly_revenue
        },
        "growth": {
            "new_organizations_30d": new_organizations,
            "new_users_30d": new_users,
            "new_bookings_30d": new_bookings
        },
        "trial_vs_paid": {
            "trial_organizations": trial_orgs,
            "paid_organizations": paid_orgs
        },
        "top_organizations": [
            {
                "name": org.name,
                "slug": org.slug,
                "user_count": org.user_count or 0,
                "team_count": org.team_count or 0
            }
            for org in top_orgs
        ]
    }


@router.get("/saas/organizations", response_model=List[OrganizationWithStats])
async def list_all_organizations(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    has_subscription: Optional[bool] = None,
    subscription_status: Optional[str] = None,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """List all organizations with advanced filtering"""
    
    query = db.query(Organization)
    
    # Basic filters
    if search:
        query = query.filter(
            Organization.name.ilike(f"%{search}%") |
            Organization.slug.ilike(f"%{search}%") |
            Organization.contact_email.ilike(f"%{search}%")
        )
    
    if is_active is not None:
        query = query.filter(Organization.is_active == is_active)
    
    # Subscription filters
    if has_subscription is not None:
        if has_subscription:
            query = query.join(Subscription)
        else:
            query = query.outerjoin(Subscription).filter(Subscription.id.is_(None))
    
    if subscription_status:
        query = query.join(Subscription).filter(Subscription.status == subscription_status)
    
    organizations = query.order_by(Organization.created_at.desc()).offset(skip).limit(limit).all()
    
    # Enhance with stats
    result = []
    for org in organizations:
        user_count = db.query(User).filter(User.organization_id == org.id).count()
        team_count = db.query(Team).filter(Team.organization_id == org.id).count()
        booking_count = db.query(Booking).join(User).filter(User.organization_id == org.id).count()
        
        subscription = db.query(Subscription).filter(
            Subscription.organization_id == org.id
        ).first()
        
        license_info = db.query(License).filter(
            License.organization_id == org.id
        ).first()
        
        # Calculate revenue
        monthly_revenue = 0
        if subscription and subscription.status == "active":
            monthly_revenue = float(subscription.licensed_users * subscription.price_per_user)
        
        org_stats = OrganizationWithStats(
            **org.__dict__,
            user_count=user_count,
            team_count=team_count,
            active_subscription=subscription,
            current_license=license_info,
            usage_stats={
                "users": user_count,
                "teams": team_count,
                "bookings": booking_count,
                "monthly_revenue": monthly_revenue,
                "max_users": license_info.max_users if license_info else 0,
                "max_teams": license_info.max_teams if license_info else 0
            }
        )
        result.append(org_stats)
    
    return result


@router.get("/saas/organizations/{organization_id}")
async def get_organization_details(
    organization_id: int,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """Get detailed organization information"""
    
    organization = db.query(Organization).filter(
        Organization.id == organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get comprehensive stats
    users = db.query(User).filter(User.organization_id == organization_id).all()
    teams = db.query(Team).filter(Team.organization_id == organization_id).all()
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization_id
    ).first()
    license_info = db.query(License).filter(
        License.organization_id == organization_id
    ).first()
    
    # Recent activity
    recent_users = db.query(User).filter(
        and_(
            User.organization_id == organization_id,
            User.created_at >= datetime.utcnow() - timedelta(days=30)
        )
    ).order_by(User.created_at.desc()).limit(10).all()
    
    recent_bookings = db.query(Booking).join(User).filter(
        and_(
            User.organization_id == organization_id,
            Booking.created_at >= datetime.utcnow() - timedelta(days=30)
        )
    ).order_by(Booking.created_at.desc()).limit(10).all()
    
    # Usage over time (last 30 days)
    usage_logs = db.query(UsageLog).filter(
        and_(
            UsageLog.organization_id == organization_id,
            UsageLog.metric_date >= datetime.utcnow() - timedelta(days=30)
        )
    ).order_by(UsageLog.metric_date.desc()).all()
    
    return {
        "organization": organization,
        "stats": {
            "total_users": len(users),
            "active_users": len([u for u in users if u.is_active]),
            "total_teams": len(teams),
            "active_teams": len([t for t in teams if t.is_active])
        },
        "subscription": subscription,
        "license": license_info,
        "recent_activity": {
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "created_at": u.created_at
                }
                for u in recent_users
            ],
            "bookings": [
                {
                    "id": b.id,
                    "title": b.title,
                    "start_time": b.start_time,
                    "status": b.status,
                    "created_at": b.created_at
                }
                for b in recent_bookings
            ]
        },
        "usage_history": [
            {
                "date": log.metric_date,
                "metric": log.metric_name,
                "value": log.metric_value,
                "metadata": log.metadata
            }
            for log in usage_logs
        ]
    }


@router.put("/saas/organizations/{organization_id}/status")
async def update_organization_status(
    organization_id: int,
    is_active: bool,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """Activate or deactivate an organization"""
    
    organization = db.query(Organization).filter(
        Organization.id == organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    organization.is_active = is_active
    db.commit()
    
    # Update license status
    licensing_service = LicensingService(db)
    if is_active:
        await licensing_service.activate_license(organization_id)
    else:
        await licensing_service.deactivate_license(organization_id)
    
    status = "activated" if is_active else "deactivated"
    return {
        "status": "success",
        "message": f"Organization {status} successfully"
    }


@router.post("/saas/organizations/{organization_id}/subscription/cancel")
async def cancel_organization_subscription(
    organization_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """Cancel organization subscription"""
    
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    try:
        billing_service = BillingService(db)
        cancelled_subscription = await billing_service.cancel_subscription(subscription)
        
        return {
            "status": "success",
            "message": "Subscription cancelled successfully",
            "subscription_id": cancelled_subscription.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/saas/subscriptions")
async def list_all_subscriptions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """List all subscriptions"""
    
    query = db.query(Subscription).join(Organization)
    
    if status:
        query = query.filter(Subscription.status == status)
    
    subscriptions = query.order_by(
        Subscription.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for sub in subscriptions:
        organization = db.query(Organization).filter(
            Organization.id == sub.organization_id
        ).first()
        
        result.append({
            "subscription": sub,
            "organization": {
                "id": organization.id,
                "name": organization.name,
                "slug": organization.slug,
                "contact_email": organization.contact_email
            },
            "monthly_revenue": float(sub.licensed_users * sub.price_per_user) if sub.status == "active" else 0
        })
    
    return result


@router.get("/saas/revenue")
async def get_revenue_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """Get revenue analytics"""
    
    # Current month revenue
    current_month_revenue = db.query(
        func.sum(Subscription.licensed_users * Subscription.price_per_user)
    ).filter(
        Subscription.status == "active"
    ).scalar() or 0
    
    # Daily revenue over specified period
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get subscription changes over time
    daily_revenue = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        
        # Calculate revenue for this date
        # (This is simplified - in reality you'd track daily snapshots)
        revenue = db.query(
            func.sum(Subscription.licensed_users * Subscription.price_per_user)
        ).filter(
            and_(
                Subscription.status == "active",
                Subscription.created_at <= date
            )
        ).scalar() or 0
        
        daily_revenue.append({
            "date": date.strftime('%Y-%m-%d'),
            "revenue": float(revenue)
        })
    
    # Revenue by plan
    revenue_by_plan = db.query(
        Subscription.plan_name,
        func.count(Subscription.id).label('subscription_count'),
        func.sum(Subscription.licensed_users).label('total_users'),
        func.sum(Subscription.licensed_users * Subscription.price_per_user).label('total_revenue')
    ).filter(
        Subscription.status == "active"
    ).group_by(Subscription.plan_name).all()
    
    return {
        "current_month_revenue": float(current_month_revenue),
        "daily_revenue": daily_revenue,
        "revenue_by_plan": [
            {
                "plan": plan.plan_name,
                "subscriptions": plan.subscription_count,
                "users": plan.total_users,
                "revenue": float(plan.total_revenue)
            }
            for plan in revenue_by_plan
        ]
    }


@router.get("/saas/usage")
async def get_usage_analytics(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """Get system-wide usage analytics"""
    
    # Usage by organization
    org_usage = db.query(
        Organization.name,
        Organization.slug,
        func.count(User.id).label('users'),
        func.count(Team.id).label('teams')
    ).outerjoin(User).outerjoin(Team).group_by(
        Organization.id, Organization.name, Organization.slug
    ).order_by(desc('users')).limit(20).all()
    
    # Usage trends (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    usage_trends = db.query(
        func.date(UsageLog.metric_date).label('date'),
        UsageLog.metric_name,
        func.sum(UsageLog.metric_value).label('total_value')
    ).filter(
        UsageLog.metric_date >= thirty_days_ago
    ).group_by(
        func.date(UsageLog.metric_date),
        UsageLog.metric_name
    ).order_by('date').all()
    
    # Process trends data
    trends_by_metric = {}
    for trend in usage_trends:
        metric = trend.metric_name
        if metric not in trends_by_metric:
            trends_by_metric[metric] = []
        trends_by_metric[metric].append({
            "date": trend.date.strftime('%Y-%m-%d'),
            "value": trend.total_value
        })
    
    return {
        "top_organizations": [
            {
                "name": org.name,
                "slug": org.slug,
                "users": org.users or 0,
                "teams": org.teams or 0
            }
            for org in org_usage
        ],
        "usage_trends": trends_by_metric
    }


@router.post("/saas/maintenance")
async def trigger_maintenance_tasks(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_system_admin)
):
    """Trigger maintenance tasks"""
    
    background_tasks.add_task(run_maintenance_tasks, db)
    
    return {
        "status": "success",
        "message": "Maintenance tasks scheduled"
    }


# Background tasks
async def run_maintenance_tasks(db: Session):
    """Run system maintenance tasks"""
    
    try:
        # Update usage statistics for all organizations
        usage_service = UsageTrackingService(db)
        await usage_service.update_all_organizations_usage()
        
        # Clean up old usage logs (keep last 90 days)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        db.query(UsageLog).filter(
            UsageLog.metric_date < ninety_days_ago
        ).delete()
        
        # Deactivate expired trial organizations
        expired_trials = db.query(Organization).filter(
            and_(
                Organization.trial_end_date < datetime.utcnow(),
                Organization.is_active == True
            )
        ).all()
        
        for org in expired_trials:
            # Check if they have active subscription
            subscription = db.query(Subscription).filter(
                and_(
                    Subscription.organization_id == org.id,
                    Subscription.status.in_(["active", "trialing"])
                )
            ).first()
            
            if not subscription:
                org.is_active = False
                
                # Deactivate license
                licensing_service = LicensingService(db)
                await licensing_service.deactivate_license(org.id)
        
        db.commit()
        
    except Exception as e:
        import logging
        logging.error(f"Maintenance task error: {str(e)}")
        db.rollback()
