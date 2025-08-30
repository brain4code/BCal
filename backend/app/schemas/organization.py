from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from decimal import Decimal


# Organization Schemas
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, regex="^[a-z0-9-]+$")
    description: Optional[str] = None
    contact_email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    max_users: int = Field(default=5, ge=1, le=10000)
    
    # White Labeling
    custom_domain: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = Field(default="#3B82F6", regex=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: str = Field(default="#1F2937", regex=r'^#[0-9A-Fa-f]{6}$')
    accent_color: str = Field(default="#10B981", regex=r'^#[0-9A-Fa-f]{6}$')
    
    # Branding
    brand_name: Optional[str] = None
    brand_tagline: Optional[str] = None
    custom_css: Optional[str] = None
    
    # Email Settings
    custom_email_from: Optional[str] = None
    email_signature: Optional[str] = None
    
    # Feature Flags
    features: Dict[str, Any] = Field(default_factory=lambda: {
        "teams": True,
        "calendar_integration": True,
        "email_notifications": True,
        "sms_notifications": False,
        "video_conferencing": True,
        "custom_branding": True,
        "api_access": True,
        "advanced_analytics": False
    })


class OrganizationCreate(OrganizationBase):
    trial_days: int = Field(default=14, ge=0, le=90)


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    contact_email: Optional[str] = Field(None, regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    max_users: Optional[int] = Field(None, ge=1, le=10000)
    
    # White Labeling
    custom_domain: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    accent_color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    
    # Branding
    brand_name: Optional[str] = None
    brand_tagline: Optional[str] = None
    custom_css: Optional[str] = None
    
    # Email Settings
    custom_email_from: Optional[str] = None
    email_signature: Optional[str] = None
    
    # Feature Flags
    features: Optional[Dict[str, Any]] = None
    
    is_active: Optional[bool] = None


class Organization(OrganizationBase):
    id: int
    is_active: bool
    trial_end_date: Optional[datetime]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Subscription Schemas
class SubscriptionBase(BaseModel):
    plan_name: str = Field(default="standard")
    price_per_user: Decimal = Field(default=Decimal("2.99"), ge=0)
    billing_cycle: str = Field(default="monthly", regex="^(monthly|yearly)$")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    licensed_users: int = Field(default=0, ge=0)


class SubscriptionCreate(SubscriptionBase):
    organization_id: int


class SubscriptionUpdate(BaseModel):
    plan_name: Optional[str] = None
    price_per_user: Optional[Decimal] = Field(None, ge=0)
    billing_cycle: Optional[str] = Field(None, regex="^(monthly|yearly)$")
    licensed_users: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, regex="^(active|cancelled|past_due|unpaid)$")


class Subscription(SubscriptionBase):
    id: int
    organization_id: int
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    stripe_price_id: Optional[str]
    status: str
    trial_days: int
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    next_billing_date: Optional[datetime]
    active_users: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# License Schemas
class LicenseBase(BaseModel):
    license_type: str = Field(default="standard")
    max_users: int = Field(default=5, ge=1)
    max_teams: int = Field(default=10, ge=1)
    max_bookings_per_month: int = Field(default=1000, ge=1)
    allowed_features: List[str] = Field(default=[
        "basic_booking",
        "team_management", 
        "email_notifications",
        "calendar_integration"
    ])


class LicenseCreate(LicenseBase):
    organization_id: int
    expires_date: Optional[datetime] = None


class LicenseUpdate(BaseModel):
    license_type: Optional[str] = None
    max_users: Optional[int] = Field(None, ge=1)
    max_teams: Optional[int] = Field(None, ge=1)
    max_bookings_per_month: Optional[int] = Field(None, ge=1)
    expires_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    allowed_features: Optional[List[str]] = None


class License(LicenseBase):
    id: int
    organization_id: int
    license_key: str
    issued_date: datetime
    expires_date: Optional[datetime]
    is_active: bool
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Usage Log Schemas
class UsageLogCreate(BaseModel):
    organization_id: int
    metric_name: str = Field(..., min_length=1)
    metric_value: int = Field(default=0, ge=0)
    metric_date: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UsageLog(BaseModel):
    id: int
    organization_id: int
    metric_name: str
    metric_value: int
    metric_date: datetime
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# Response Schemas
class OrganizationWithStats(Organization):
    user_count: int
    team_count: int
    active_subscription: Optional[Subscription] = None
    current_license: Optional[License] = None
    usage_stats: Dict[str, Any] = Field(default_factory=dict)


class LicenseValidationResponse(BaseModel):
    valid: bool
    license: Optional[License] = None
    organization: Optional[Organization] = None
    errors: List[str] = Field(default_factory=list)
    remaining_users: int = 0
    remaining_teams: int = 0
    remaining_bookings: int = 0


# Tenant Context
class TenantContext(BaseModel):
    organization_id: Optional[int] = None
    organization_slug: Optional[str] = None
    custom_domain: Optional[str] = None
    is_system_admin: bool = False
    user_id: Optional[int] = None
    user_role: Optional[str] = None
