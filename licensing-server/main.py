from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, JSON, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import secrets
import hashlib
import hmac
import os
import httpx
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://license_user:license_password@postgres:5432/license_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
security = HTTPBearer()
LICENSE_SERVER_SECRET = os.getenv("LICENSE_SERVER_SECRET", "licensing-secret-key-change-in-production")


# Database Models
class LicenseEntry(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, unique=True, index=True, nullable=False)
    organization_id = Column(Integer, nullable=False, index=True)
    organization_name = Column(String, nullable=False)
    
    # License Details
    license_type = Column(String, default="standard")  # standard, enterprise, trial
    max_users = Column(Integer, default=5)
    max_teams = Column(Integer, default=10)
    max_bookings_per_month = Column(Integer, default=1000)
    
    # Status
    is_active = Column(Boolean, default=True)
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    expires_date = Column(DateTime(timezone=True), nullable=True)
    
    # Features
    allowed_features = Column(JSON, default=[
        "basic_booking", "team_management", 
        "email_notifications", "calendar_integration"
    ])
    
    # Usage Tracking
    current_users = Column(Integer, default=0)
    current_teams = Column(Integer, default=0)
    monthly_bookings = Column(Integer, default=0)
    last_usage_update = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, nullable=False, index=True)
    organization_id = Column(Integer, nullable=False)
    
    # Usage Data
    users_count = Column(Integer, default=0)
    teams_count = Column(Integer, default=0)
    bookings_count = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)
    
    # Billing
    billing_amount = Column(Numeric(10, 2), default=0)
    billing_period_start = Column(DateTime(timezone=True), nullable=False)
    billing_period_end = Column(DateTime(timezone=True), nullable=False)
    
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())


# Pydantic Models
class LicenseCreate(BaseModel):
    organization_id: int
    organization_name: str
    license_type: str = "standard"
    max_users: int = 5
    max_teams: int = 10
    max_bookings_per_month: int = 1000
    expires_date: Optional[datetime] = None
    allowed_features: List[str] = Field(default=[
        "basic_booking", "team_management", 
        "email_notifications", "calendar_integration"
    ])


class LicenseValidation(BaseModel):
    license_key: str
    organization_id: int
    feature: Optional[str] = None


class LicenseResponse(BaseModel):
    license_key: str
    organization_id: int
    organization_name: str
    license_type: str
    max_users: int
    max_teams: int
    max_bookings_per_month: int
    is_active: bool
    expires_date: Optional[datetime]
    allowed_features: List[str]
    current_usage: Dict[str, int]


class ValidationResponse(BaseModel):
    valid: bool
    license: Optional[LicenseResponse] = None
    errors: List[str] = Field(default_factory=list)
    remaining_users: int = 0
    remaining_teams: int = 0
    remaining_bookings: int = 0


class UsageUpdate(BaseModel):
    license_key: str
    organization_id: int
    users_count: int = 0
    teams_count: int = 0
    bookings_count: int = 0
    api_calls: int = 0


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Security functions
def generate_license_key(organization_id: int, organization_name: str) -> str:
    """Generate a unique license key"""
    timestamp = int(datetime.utcnow().timestamp())
    data = f"{organization_id}-{organization_name}-{timestamp}"
    random_suffix = secrets.token_hex(8)
    
    # Create hash
    hash_obj = hashlib.sha256(f"{data}-{random_suffix}".encode())
    hash_hex = hash_obj.hexdigest()[:16].upper()
    
    # Format as license key: BCAL-XXXX-XXXX-XXXX-XXXX
    formatted = f"BCAL-{hash_hex[:4]}-{hash_hex[4:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}"
    return formatted


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for licensing server access"""
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
    
    # In production, implement proper API key management
    expected_key = os.getenv("LICENSING_API_KEY", "licensing-api-key-change-in-production")
    if credentials.credentials != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return credentials


# Startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting BCal Licensing Server...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    yield
    # Shutdown
    logger.info("Shutting down BCal Licensing Server...")


# FastAPI app
app = FastAPI(
    title="BCal Licensing Server",
    description="License validation and billing service for BCal SAAS",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bcal-licensing-server"}


@app.post("/licenses", response_model=LicenseResponse)
async def create_license(
    license_data: LicenseCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
):
    """Create a new license"""
    
    # Check if organization already has a license
    existing = db.query(LicenseEntry).filter(
        LicenseEntry.organization_id == license_data.organization_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Organization already has a license"
        )
    
    # Generate license key
    license_key = generate_license_key(
        license_data.organization_id, 
        license_data.organization_name
    )
    
    # Create license
    license_entry = LicenseEntry(
        license_key=license_key,
        organization_id=license_data.organization_id,
        organization_name=license_data.organization_name,
        license_type=license_data.license_type,
        max_users=license_data.max_users,
        max_teams=license_data.max_teams,
        max_bookings_per_month=license_data.max_bookings_per_month,
        expires_date=license_data.expires_date,
        allowed_features=license_data.allowed_features
    )
    
    db.add(license_entry)
    db.commit()
    db.refresh(license_entry)
    
    logger.info(f"Created license {license_key} for organization {license_data.organization_id}")
    
    return LicenseResponse(
        license_key=license_entry.license_key,
        organization_id=license_entry.organization_id,
        organization_name=license_entry.organization_name,
        license_type=license_entry.license_type,
        max_users=license_entry.max_users,
        max_teams=license_entry.max_teams,
        max_bookings_per_month=license_entry.max_bookings_per_month,
        is_active=license_entry.is_active,
        expires_date=license_entry.expires_date,
        allowed_features=license_entry.allowed_features,
        current_usage={
            "users": license_entry.current_users,
            "teams": license_entry.current_teams,
            "bookings": license_entry.monthly_bookings
        }
    )


@app.post("/validate", response_model=ValidationResponse)
async def validate_license(
    validation: LicenseValidation,
    db: Session = Depends(get_db)
):
    """Validate a license"""
    
    license_entry = db.query(LicenseEntry).filter(
        LicenseEntry.license_key == validation.license_key,
        LicenseEntry.organization_id == validation.organization_id
    ).first()
    
    if not license_entry:
        return ValidationResponse(
            valid=False,
            errors=["License not found"]
        )
    
    errors = []
    
    # Check if license is active
    if not license_entry.is_active:
        errors.append("License is inactive")
    
    # Check expiration
    if license_entry.expires_date and license_entry.expires_date < datetime.utcnow():
        errors.append("License has expired")
    
    # Check feature access
    if validation.feature and validation.feature not in license_entry.allowed_features:
        errors.append(f"Feature '{validation.feature}' not allowed")
    
    is_valid = len(errors) == 0
    
    response = ValidationResponse(
        valid=is_valid,
        errors=errors,
        remaining_users=max(0, license_entry.max_users - license_entry.current_users),
        remaining_teams=max(0, license_entry.max_teams - license_entry.current_teams),
        remaining_bookings=max(0, license_entry.max_bookings_per_month - license_entry.monthly_bookings)
    )
    
    if is_valid:
        response.license = LicenseResponse(
            license_key=license_entry.license_key,
            organization_id=license_entry.organization_id,
            organization_name=license_entry.organization_name,
            license_type=license_entry.license_type,
            max_users=license_entry.max_users,
            max_teams=license_entry.max_teams,
            max_bookings_per_month=license_entry.max_bookings_per_month,
            is_active=license_entry.is_active,
            expires_date=license_entry.expires_date,
            allowed_features=license_entry.allowed_features,
            current_usage={
                "users": license_entry.current_users,
                "teams": license_entry.current_teams,
                "bookings": license_entry.monthly_bookings
            }
        )
    
    return response


@app.post("/usage")
async def update_usage(
    usage: UsageUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update usage statistics for a license"""
    
    license_entry = db.query(LicenseEntry).filter(
        LicenseEntry.license_key == usage.license_key,
        LicenseEntry.organization_id == usage.organization_id
    ).first()
    
    if not license_entry:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Update current usage
    license_entry.current_users = usage.users_count
    license_entry.current_teams = usage.teams_count
    license_entry.monthly_bookings = usage.bookings_count
    license_entry.last_usage_update = datetime.utcnow()
    
    db.commit()
    
    # Record usage for billing (background task)
    background_tasks.add_task(
        record_usage_for_billing,
        db,
        usage
    )
    
    return {"status": "success", "message": "Usage updated"}


@app.get("/licenses/{organization_id}", response_model=LicenseResponse)
async def get_license(
    organization_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
):
    """Get license details for an organization"""
    
    license_entry = db.query(LicenseEntry).filter(
        LicenseEntry.organization_id == organization_id
    ).first()
    
    if not license_entry:
        raise HTTPException(status_code=404, detail="License not found")
    
    return LicenseResponse(
        license_key=license_entry.license_key,
        organization_id=license_entry.organization_id,
        organization_name=license_entry.organization_name,
        license_type=license_entry.license_type,
        max_users=license_entry.max_users,
        max_teams=license_entry.max_teams,
        max_bookings_per_month=license_entry.max_bookings_per_month,
        is_active=license_entry.is_active,
        expires_date=license_entry.expires_date,
        allowed_features=license_entry.allowed_features,
        current_usage={
            "users": license_entry.current_users,
            "teams": license_entry.current_teams,
            "bookings": license_entry.monthly_bookings
        }
    )


@app.put("/licenses/{organization_id}/status")
async def update_license_status(
    organization_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
):
    """Update license status (activate/deactivate)"""
    
    license_entry = db.query(LicenseEntry).filter(
        LicenseEntry.organization_id == organization_id
    ).first()
    
    if not license_entry:
        raise HTTPException(status_code=404, detail="License not found")
    
    license_entry.is_active = is_active
    db.commit()
    
    status = "activated" if is_active else "deactivated"
    logger.info(f"License {license_entry.license_key} {status}")
    
    return {"status": "success", "message": f"License {status}"}


# Background tasks
async def record_usage_for_billing(db: Session, usage: UsageUpdate):
    """Record usage for billing purposes"""
    try:
        # Calculate billing period (current month)
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1) - timedelta(seconds=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1) - timedelta(seconds=1)
        
        # Check if record exists for this billing period
        existing_record = db.query(UsageRecord).filter(
            UsageRecord.license_key == usage.license_key,
            UsageRecord.billing_period_start == period_start
        ).first()
        
        if existing_record:
            # Update existing record
            existing_record.users_count = usage.users_count
            existing_record.teams_count = usage.teams_count
            existing_record.bookings_count = usage.bookings_count
            existing_record.api_calls = usage.api_calls
            existing_record.billing_amount = usage.users_count * 2.99  # $2.99 per user
        else:
            # Create new record
            usage_record = UsageRecord(
                license_key=usage.license_key,
                organization_id=usage.organization_id,
                users_count=usage.users_count,
                teams_count=usage.teams_count,
                bookings_count=usage.bookings_count,
                api_calls=usage.api_calls,
                billing_amount=usage.users_count * 2.99,
                billing_period_start=period_start,
                billing_period_end=period_end
            )
            db.add(usage_record)
        
        db.commit()
        logger.info(f"Usage recorded for license {usage.license_key}")
        
    except Exception as e:
        logger.error(f"Error recording usage: {str(e)}")
        db.rollback()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
