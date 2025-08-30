from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://bcal_user:bcal_password@localhost:5432/bcal_db"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    
    # App
    app_name: str = "BCal API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Authentication Configuration
    auth_provider: str = "local"  # local, auth0, generic_sso
    auth0_domain: Optional[str] = None
    auth0_client_id: Optional[str] = None
    auth0_client_secret: Optional[str] = None
    auth0_audience: Optional[str] = None
    
    # Generic SSO Configuration
    sso_issuer_url: Optional[str] = None
    sso_client_id: Optional[str] = None
    sso_client_secret: Optional[str] = None
    sso_redirect_uri: Optional[str] = None
    
    # Email Configuration
    email_enabled: bool = False
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from: str = "noreply@bcal.com"
    email_use_tls: bool = True
    
    # Google Calendar Integration
    google_calendar_enabled: bool = False
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    
    # Payment Configuration
    stripe_enabled: bool = False
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # Licensing Server Configuration
    licensing_server_url: str = "http://licensing-server:8001"
    licensing_api_key: str = "licensing-api-key-change-in-production"
    
    # Multi-tenant Configuration
    enable_multi_tenancy: bool = True
    default_organization_name: str = "Default Organization"
    trial_days: int = 14
    max_organizations: int = 1000
    
    # Video Conferencing
    video_conferencing_enabled: bool = False
    zoom_api_key: Optional[str] = None
    zoom_api_secret: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    
    # Booking Rules
    min_notice_hours: int = 2  # Minimum notice period in hours
    max_booking_days: int = 90  # Maximum days in advance to book
    buffer_minutes: int = 15  # Buffer time between meetings
    slot_duration_minutes: int = 30  # Default slot duration
    
    class Config:
        env_file = ".env"


settings = Settings()
