from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Availability(Base):
    __tablename__ = "availabilities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String, nullable=False)  # Format: "HH:MM"
    end_time = Column(String, nullable=False)  # Format: "HH:MM"
    is_active = Column(Boolean, default=True)
    
    # Recurring pattern support
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)  # daily, weekly, monthly
    recurring_end_date = Column(DateTime(timezone=True), nullable=True)
    recurring_days = Column(JSON, nullable=True)  # [1,3,5] for specific days
    
    # Advanced booking rules
    buffer_before_minutes = Column(Integer, default=0)
    buffer_after_minutes = Column(Integer, default=0)
    min_notice_hours = Column(Integer, default=2)
    max_booking_days = Column(Integer, default=90)
    slot_duration_minutes = Column(Integer, default=30)
    
    # Calendar integration
    sync_with_calendar = Column(Boolean, default=False)
    calendar_id = Column(String, nullable=True)
    
    # Meeting settings
    meeting_type = Column(String, default="general")  # general, consultation, interview, etc.
    meeting_description = Column(Text, nullable=True)
    meeting_location = Column(String, nullable=True)  # physical address or video call
    meeting_url = Column(String, nullable=True)  # video call URL
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="availabilities")
