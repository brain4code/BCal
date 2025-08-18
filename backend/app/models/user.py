from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for SSO users
    is_active = Column(Boolean, default=True)
    role = Column(String, default="visitor")  # visitor, user, admin
    timezone = Column(String, default="UTC")
    bio = Column(Text, nullable=True)
    
    # SSO Authentication fields
    auth0_user_id = Column(String, unique=True, nullable=True)
    sso_user_id = Column(String, unique=True, nullable=True)
    auth_provider = Column(String, default="local")  # local, auth0, generic_sso
    
    # Profile fields
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    position = Column(String, nullable=True)
    website = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    reminder_preferences = Column(String, default="24h,1h")  # JSON string of reminder times
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    availabilities = relationship("Availability", back_populates="user", cascade="all, delete-orphan")
    bookings_as_host = relationship("Booking", foreign_keys="Booking.host_id", back_populates="host")
    bookings_as_guest = relationship("Booking", foreign_keys="Booking.guest_id", back_populates="guest")
    team_memberships = relationship("TeamMember", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
