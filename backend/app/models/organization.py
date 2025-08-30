from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)  # URL-friendly identifier
    description = Column(Text, nullable=True)
    
    # Contact Information
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    
    # Status and Settings
    is_active = Column(Boolean, default=True)
    trial_end_date = Column(DateTime(timezone=True), nullable=True)
    max_users = Column(Integer, default=5)  # License limit
    
    # White Labeling
    custom_domain = Column(String, nullable=True, unique=True)
    logo_url = Column(String, nullable=True)
    favicon_url = Column(String, nullable=True)
    primary_color = Column(String, default="#3B82F6")  # Default blue
    secondary_color = Column(String, default="#1F2937")  # Default gray
    accent_color = Column(String, default="#10B981")  # Default green
    
    # Branding
    brand_name = Column(String, nullable=True)  # Custom app name
    brand_tagline = Column(String, nullable=True)
    custom_css = Column(Text, nullable=True)
    
    # Email Settings
    custom_email_from = Column(String, nullable=True)
    email_signature = Column(Text, nullable=True)
    
    # Feature Flags
    features = Column(JSON, default={
        "teams": True,
        "calendar_integration": True,
        "email_notifications": True,
        "sms_notifications": False,
        "video_conferencing": True,
        "custom_branding": True,
        "api_access": True,
        "advanced_analytics": False
    })
    
    # Metadata
    metadata = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="organization")
    teams = relationship("Team", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization")
    licenses = relationship("License", back_populates="organization")
    usage_logs = relationship("UsageLog", back_populates="organization")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    
    # Stripe Integration
    stripe_customer_id = Column(String, unique=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    stripe_price_id = Column(String, nullable=True)
    
    # Subscription Details
    plan_name = Column(String, default="standard")  # standard, enterprise
    price_per_user = Column(Numeric(10, 2), default=2.99)
    billing_cycle = Column(String, default="monthly")  # monthly, yearly
    currency = Column(String, default="USD")
    
    # Status
    status = Column(String, default="active")  # active, cancelled, past_due, unpaid
    trial_days = Column(Integer, default=14)
    
    # Billing
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    
    # User Count
    licensed_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="subscriptions")


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    
    # License Key
    license_key = Column(String, unique=True, nullable=False, index=True)
    license_type = Column(String, default="standard")  # standard, enterprise, trial
    
    # Limits
    max_users = Column(Integer, default=5)
    max_teams = Column(Integer, default=10)
    max_bookings_per_month = Column(Integer, default=1000)
    
    # Validity
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    expires_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Features
    allowed_features = Column(JSON, default=[
        "basic_booking",
        "team_management",
        "email_notifications",
        "calendar_integration"
    ])
    
    # Metadata
    metadata = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="licenses")


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    
    # Usage Metrics
    metric_name = Column(String, nullable=False)  # active_users, bookings_created, api_calls
    metric_value = Column(Integer, default=0)
    metric_date = Column(DateTime(timezone=True), nullable=False)
    
    # Additional Data
    metadata = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="usage_logs")
