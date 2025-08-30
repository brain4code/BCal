import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..core.config import settings
from ..models import Organization, License
from ..schemas.organization import LicenseValidationResponse

logger = logging.getLogger(__name__)


class LicensingService:
    """Service for interacting with the licensing server"""
    
    def __init__(self, db: Session):
        self.db = db
        self.licensing_server_url = settings.licensing_server_url
        self.api_key = settings.licensing_api_key
    
    async def create_license(
        self,
        organization_id: int,
        max_users: int = 5,
        max_teams: int = 10,
        license_type: str = "standard",
        expires_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a license via the licensing server"""
        
        organization = self.db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            raise Exception("Organization not found")
        
        # Set trial expiration if not provided
        if not expires_date and license_type == "trial":
            expires_date = datetime.utcnow() + timedelta(days=14)
        
        payload = {
            "organization_id": organization_id,
            "organization_name": organization.name,
            "license_type": license_type,
            "max_users": max_users,
            "max_teams": max_teams,
            "max_bookings_per_month": 1000 if license_type == "standard" else 10000,
            "expires_date": expires_date.isoformat() if expires_date else None,
            "allowed_features": self._get_features_for_license_type(license_type)
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.licensing_server_url}/licenses",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    license_data = response.json()
                    
                    # Store license key in local database
                    license_record = License(
                        organization_id=organization_id,
                        license_key=license_data["license_key"],
                        license_type=license_type,
                        max_users=max_users,
                        max_teams=max_teams,
                        max_bookings_per_month=payload["max_bookings_per_month"],
                        expires_date=expires_date,
                        allowed_features=payload["allowed_features"]
                    )
                    
                    self.db.add(license_record)
                    self.db.commit()
                    
                    logger.info(f"Created license for organization {organization_id}")
                    return license_data
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    raise Exception(f"Licensing server error: {error_detail}")
                    
        except httpx.RequestError as e:
            logger.error(f"Failed to communicate with licensing server: {str(e)}")
            raise Exception("Licensing service unavailable")
    
    async def validate_license(
        self,
        organization_id: int,
        feature: Optional[str] = None
    ) -> LicenseValidationResponse:
        """Validate license via the licensing server"""
        
        # Get license key from local database
        license_record = self.db.query(License).filter(
            and_(
                License.organization_id == organization_id,
                License.is_active == True
            )
        ).first()
        
        if not license_record:
            return LicenseValidationResponse(
                valid=False,
                errors=["No license found for organization"]
            )
        
        payload = {
            "license_key": license_record.license_key,
            "organization_id": organization_id,
            "feature": feature
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.licensing_server_url}/validate",
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return LicenseValidationResponse(**response.json())
                else:
                    return LicenseValidationResponse(
                        valid=False,
                        errors=["License validation failed"]
                    )
                    
        except httpx.RequestError as e:
            logger.error(f"Failed to validate license: {str(e)}")
            # Fallback to local validation
            return self._validate_license_locally(license_record, feature)
    
    async def update_usage(
        self,
        organization_id: int,
        users_count: int,
        teams_count: int,
        bookings_count: int
    ) -> bool:
        """Update usage statistics in the licensing server"""
        
        license_record = self.db.query(License).filter(
            License.organization_id == organization_id
        ).first()
        
        if not license_record:
            logger.warning(f"No license found for organization {organization_id}")
            return False
        
        payload = {
            "license_key": license_record.license_key,
            "organization_id": organization_id,
            "users_count": users_count,
            "teams_count": teams_count,
            "bookings_count": bookings_count,
            "api_calls": 0  # Could be tracked separately
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.licensing_server_url}/usage",
                    json=payload,
                    timeout=10.0
                )
                
                return response.status_code == 200
                
        except httpx.RequestError as e:
            logger.error(f"Failed to update usage: {str(e)}")
            return False
    
    async def update_license_limits(
        self,
        organization_id: int,
        max_users: Optional[int] = None,
        max_teams: Optional[int] = None
    ) -> bool:
        """Update license limits (called when subscription changes)"""
        
        license_record = self.db.query(License).filter(
            License.organization_id == organization_id
        ).first()
        
        if not license_record:
            return False
        
        # Update local record
        if max_users is not None:
            license_record.max_users = max_users
        if max_teams is not None:
            license_record.max_teams = max_teams
        
        self.db.commit()
        
        # Note: In a real implementation, you might also update the licensing server
        # via an API call, but for simplicity we're updating locally here
        
        logger.info(f"Updated license limits for organization {organization_id}")
        return True
    
    async def activate_license(self, organization_id: int) -> bool:
        """Activate license"""
        
        license_record = self.db.query(License).filter(
            License.organization_id == organization_id
        ).first()
        
        if license_record:
            license_record.is_active = True
            self.db.commit()
            
            # Also update licensing server
            try:
                async with httpx.AsyncClient() as client:
                    await client.put(
                        f"{self.licensing_server_url}/licenses/{organization_id}/status",
                        params={"is_active": True},
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=10.0
                    )
            except httpx.RequestError:
                logger.warning(f"Failed to update licensing server for org {organization_id}")
            
            logger.info(f"Activated license for organization {organization_id}")
            return True
        
        return False
    
    async def deactivate_license(self, organization_id: int) -> bool:
        """Deactivate license"""
        
        license_record = self.db.query(License).filter(
            License.organization_id == organization_id
        ).first()
        
        if license_record:
            license_record.is_active = False
            self.db.commit()
            
            # Also update licensing server
            try:
                async with httpx.AsyncClient() as client:
                    await client.put(
                        f"{self.licensing_server_url}/licenses/{organization_id}/status",
                        params={"is_active": False},
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=10.0
                    )
            except httpx.RequestError:
                logger.warning(f"Failed to update licensing server for org {organization_id}")
            
            logger.info(f"Deactivated license for organization {organization_id}")
            return True
        
        return False
    
    def _get_features_for_license_type(self, license_type: str) -> list:
        """Get allowed features for license type"""
        
        base_features = [
            "basic_booking",
            "email_notifications",
            "calendar_integration"
        ]
        
        if license_type in ["standard", "enterprise"]:
            base_features.extend([
                "team_management",
                "custom_branding",
                "api_access"
            ])
        
        if license_type == "enterprise":
            base_features.extend([
                "advanced_analytics",
                "sso_integration",
                "priority_support"
            ])
        
        return base_features
    
    def _validate_license_locally(
        self,
        license_record: License,
        feature: Optional[str] = None
    ) -> LicenseValidationResponse:
        """Fallback local license validation"""
        
        errors = []
        
        # Check if license is active
        if not license_record.is_active:
            errors.append("License is inactive")
        
        # Check expiration
        if license_record.expires_date and license_record.expires_date < datetime.utcnow():
            errors.append("License has expired")
        
        # Check feature access
        if feature and feature not in license_record.allowed_features:
            errors.append(f"Feature '{feature}' not allowed")
        
        is_valid = len(errors) == 0
        
        return LicenseValidationResponse(
            valid=is_valid,
            errors=errors,
            remaining_users=license_record.max_users,  # Simplified
            remaining_teams=license_record.max_teams,
            remaining_bookings=license_record.max_bookings_per_month
        )
    
    def get_license_info(self, organization_id: int) -> Optional[License]:
        """Get license information for organization"""
        return self.db.query(License).filter(
            License.organization_id == organization_id
        ).first()
    
    def check_feature_access(self, organization_id: int, feature: str) -> bool:
        """Quick check if organization has access to a feature"""
        license_record = self.db.query(License).filter(
            and_(
                License.organization_id == organization_id,
                License.is_active == True
            )
        ).first()
        
        if not license_record:
            return False
        
        # Check expiration
        if license_record.expires_date and license_record.expires_date < datetime.utcnow():
            return False
        
        return feature in license_record.allowed_features
