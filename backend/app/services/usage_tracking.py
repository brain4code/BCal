import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Dict, Optional

from ..core.database import SessionLocal
from ..models import Organization, User, Team, Booking, UsageLog
from ..schemas.organization import UsageLogCreate
from .licensing import LicensingService

logger = logging.getLogger(__name__)


class UsageTrackingService:
    """Service for tracking and enforcing usage limits"""
    
    def __init__(self, db: Session):
        self.db = db
        self.licensing_service = LicensingService(db)
    
    async def track_user_creation(self, organization_id: int, user_id: int) -> bool:
        """Track new user creation and enforce limits"""
        
        # Get current user count
        current_users = self._get_active_user_count(organization_id)
        
        # Check license limits
        license_validation = await self.licensing_service.validate_license(organization_id)
        
        if not license_validation.valid:
            logger.warning(f"License invalid for organization {organization_id}")
            return False
        
        if license_validation.license and current_users > license_validation.license.max_users:
            logger.warning(f"User limit exceeded for organization {organization_id}")
            return False
        
        # Log usage
        await self._log_usage(
            organization_id=organization_id,
            metric_name="user_created",
            metric_value=1,
            metadata={"user_id": user_id}
        )
        
        # Update licensing server
        await self._update_licensing_server_usage(organization_id)
        
        return True
    
    async def track_team_creation(self, organization_id: int, team_id: int) -> bool:
        """Track new team creation and enforce limits"""
        
        # Get current team count
        current_teams = self._get_active_team_count(organization_id)
        
        # Check license limits
        license_validation = await self.licensing_service.validate_license(organization_id)
        
        if not license_validation.valid:
            logger.warning(f"License invalid for organization {organization_id}")
            return False
        
        if license_validation.license and current_teams > license_validation.license.max_teams:
            logger.warning(f"Team limit exceeded for organization {organization_id}")
            return False
        
        # Log usage
        await self._log_usage(
            organization_id=organization_id,
            metric_name="team_created",
            metric_value=1,
            metadata={"team_id": team_id}
        )
        
        # Update licensing server
        await self._update_licensing_server_usage(organization_id)
        
        return True
    
    async def track_booking_creation(self, organization_id: int, booking_id: int) -> bool:
        """Track new booking creation and enforce limits"""
        
        # Get current month's booking count
        current_bookings = self._get_monthly_booking_count(organization_id)
        
        # Check license limits
        license_validation = await self.licensing_service.validate_license(organization_id)
        
        if not license_validation.valid:
            logger.warning(f"License invalid for organization {organization_id}")
            return False
        
        if (license_validation.license and 
            current_bookings > license_validation.license.max_bookings_per_month):
            logger.warning(f"Booking limit exceeded for organization {organization_id}")
            return False
        
        # Log usage
        await self._log_usage(
            organization_id=organization_id,
            metric_name="booking_created",
            metric_value=1,
            metadata={"booking_id": booking_id}
        )
        
        # Update licensing server
        await self._update_licensing_server_usage(organization_id)
        
        return True
    
    async def check_feature_access(self, organization_id: int, feature: str) -> bool:
        """Check if organization has access to a specific feature"""
        
        # Use licensing service for feature validation
        license_validation = await self.licensing_service.validate_license(
            organization_id=organization_id,
            feature=feature
        )
        
        return license_validation.valid
    
    async def get_usage_summary(self, organization_id: int) -> Dict:
        """Get comprehensive usage summary for organization"""
        
        # Get current counts
        users_count = self._get_active_user_count(organization_id)
        teams_count = self._get_active_team_count(organization_id)
        monthly_bookings = self._get_monthly_booking_count(organization_id)
        
        # Get license info
        license_validation = await self.licensing_service.validate_license(organization_id)
        
        # Get historical usage (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        usage_logs = self.db.query(UsageLog).filter(
            and_(
                UsageLog.organization_id == organization_id,
                UsageLog.metric_date >= thirty_days_ago
            )
        ).all()
        
        # Process historical data
        daily_usage = {}
        for log in usage_logs:
            date_key = log.metric_date.strftime('%Y-%m-%d')
            if date_key not in daily_usage:
                daily_usage[date_key] = {}
            daily_usage[date_key][log.metric_name] = log.metric_value
        
        summary = {
            "current_usage": {
                "users": users_count,
                "teams": teams_count,
                "monthly_bookings": monthly_bookings
            },
            "limits": {},
            "remaining": {},
            "historical_usage": daily_usage,
            "license_valid": license_validation.valid,
            "license_errors": license_validation.errors
        }
        
        if license_validation.license:
            summary["limits"] = {
                "max_users": license_validation.license.max_users,
                "max_teams": license_validation.license.max_teams,
                "max_monthly_bookings": license_validation.license.max_bookings_per_month
            }
            
            summary["remaining"] = {
                "users": max(0, license_validation.license.max_users - users_count),
                "teams": max(0, license_validation.license.max_teams - teams_count),
                "bookings": max(0, license_validation.license.max_bookings_per_month - monthly_bookings)
            }
        
        return summary
    
    async def enforce_user_limit(self, organization_id: int) -> bool:
        """Check if organization can add more users"""
        
        current_users = self._get_active_user_count(organization_id)
        license_validation = await self.licensing_service.validate_license(organization_id)
        
        if not license_validation.valid:
            return False
        
        if license_validation.license:
            return current_users < license_validation.license.max_users
        
        return False
    
    async def enforce_team_limit(self, organization_id: int) -> bool:
        """Check if organization can add more teams"""
        
        current_teams = self._get_active_team_count(organization_id)
        license_validation = await self.licensing_service.validate_license(organization_id)
        
        if not license_validation.valid:
            return False
        
        if license_validation.license:
            return current_teams < license_validation.license.max_teams
        
        return False
    
    async def get_billing_usage(self, organization_id: int) -> Dict:
        """Get usage data for billing purposes"""
        
        users_count = self._get_active_user_count(organization_id)
        monthly_cost = users_count * 2.99  # $2.99 per user
        
        # Get organization for trial info
        organization = self.db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        is_trial = (organization and organization.trial_end_date and 
                   organization.trial_end_date > datetime.utcnow())
        
        return {
            "users_count": users_count,
            "monthly_cost": monthly_cost,
            "per_user_cost": 2.99,
            "is_trial": is_trial,
            "trial_end_date": organization.trial_end_date if organization else None
        }
    
    # Background task for periodic usage updates
    async def update_all_organizations_usage(self):
        """Background task to update usage for all organizations"""
        
        organizations = self.db.query(Organization).filter(
            Organization.is_active == True
        ).all()
        
        for org in organizations:
            try:
                await self._update_licensing_server_usage(org.id)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to update usage for org {org.id}: {str(e)}")
    
    # Private methods
    def _get_active_user_count(self, organization_id: int) -> int:
        """Get count of active users in organization"""
        return self.db.query(User).filter(
            and_(
                User.organization_id == organization_id,
                User.is_active == True
            )
        ).count()
    
    def _get_active_team_count(self, organization_id: int) -> int:
        """Get count of active teams in organization"""
        return self.db.query(Team).filter(
            and_(
                Team.organization_id == organization_id,
                Team.is_active == True
            )
        ).count()
    
    def _get_monthly_booking_count(self, organization_id: int) -> int:
        """Get count of bookings in current month"""
        # Calculate current month start
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Count bookings created this month for users in the organization
        return self.db.query(Booking).join(User, Booking.host_id == User.id).filter(
            and_(
                User.organization_id == organization_id,
                Booking.created_at >= month_start
            )
        ).count()
    
    async def _log_usage(
        self,
        organization_id: int,
        metric_name: str,
        metric_value: int,
        metadata: Optional[Dict] = None
    ):
        """Log usage event"""
        
        usage_log = UsageLog(
            organization_id=organization_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_date=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.db.add(usage_log)
        self.db.commit()
    
    async def _update_licensing_server_usage(self, organization_id: int):
        """Update usage statistics in licensing server"""
        
        users_count = self._get_active_user_count(organization_id)
        teams_count = self._get_active_team_count(organization_id)
        bookings_count = self._get_monthly_booking_count(organization_id)
        
        try:
            await self.licensing_service.update_usage(
                organization_id=organization_id,
                users_count=users_count,
                teams_count=teams_count,
                bookings_count=bookings_count
            )
        except Exception as e:
            logger.error(f"Failed to update licensing server usage: {str(e)}")


# Middleware decorator for feature access control
def require_feature(feature_name: str):
    """Decorator to require specific feature access"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract context from kwargs (assumes context is passed as dependency)
            context = kwargs.get('context')
            if not context or not context.organization_id:
                raise HTTPException(status_code=403, detail="Organization access required")
            
            # Check feature access
            db = kwargs.get('db')
            if db:
                usage_service = UsageTrackingService(db)
                has_access = await usage_service.check_feature_access(
                    context.organization_id, 
                    feature_name
                )
                
                if not has_access:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Feature '{feature_name}' not available in your plan"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Background task runner
async def start_usage_tracking_worker():
    """Start background worker for usage tracking"""
    
    while True:
        try:
            db = SessionLocal()
            usage_service = UsageTrackingService(db)
            await usage_service.update_all_organizations_usage()
            db.close()
            
            # Run every hour
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Usage tracking worker error: {str(e)}")
            await asyncio.sleep(60)  # Retry after 1 minute on error
