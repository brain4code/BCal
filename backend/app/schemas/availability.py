from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AvailabilityBase(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # Format: "HH:MM"
    end_time: str  # Format: "HH:MM"


class AvailabilityCreate(AvailabilityBase):
    is_active: Optional[bool] = True
    
    # Recurring pattern support
    is_recurring: Optional[bool] = False
    recurring_pattern: Optional[str] = None  # daily, weekly, monthly
    recurring_end_date: Optional[datetime] = None
    recurring_days: Optional[List[int]] = None  # [1,3,5] for specific days
    
    # Advanced booking rules
    buffer_before_minutes: Optional[int] = 0
    buffer_after_minutes: Optional[int] = 0
    min_notice_hours: Optional[int] = 2
    max_booking_days: Optional[int] = 90
    slot_duration_minutes: Optional[int] = 30
    
    # Calendar integration
    sync_with_calendar: Optional[bool] = False
    calendar_id: Optional[str] = None
    
    # Meeting settings
    meeting_type: Optional[str] = "general"  # general, consultation, interview, etc.
    meeting_description: Optional[str] = None
    meeting_location: Optional[str] = None  # physical address or video call
    meeting_url: Optional[str] = None  # video call URL


class AvailabilityUpdate(BaseModel):
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Recurring pattern support
    is_recurring: Optional[bool] = None
    recurring_pattern: Optional[str] = None
    recurring_end_date: Optional[datetime] = None
    recurring_days: Optional[List[int]] = None
    
    # Advanced booking rules
    buffer_before_minutes: Optional[int] = None
    buffer_after_minutes: Optional[int] = None
    min_notice_hours: Optional[int] = None
    max_booking_days: Optional[int] = None
    slot_duration_minutes: Optional[int] = None
    
    # Calendar integration
    sync_with_calendar: Optional[bool] = None
    calendar_id: Optional[str] = None
    
    # Meeting settings
    meeting_type: Optional[str] = None
    meeting_description: Optional[str] = None
    meeting_location: Optional[str] = None
    meeting_url: Optional[str] = None


class AvailabilityInDB(AvailabilityBase):
    id: int
    user_id: int
    is_active: bool
    
    # Recurring pattern support
    is_recurring: bool
    recurring_pattern: Optional[str]
    recurring_end_date: Optional[datetime]
    recurring_days: Optional[List[int]]
    
    # Advanced booking rules
    buffer_before_minutes: int
    buffer_after_minutes: int
    min_notice_hours: int
    max_booking_days: int
    slot_duration_minutes: int
    
    # Calendar integration
    sync_with_calendar: bool
    calendar_id: Optional[str]
    
    # Meeting settings
    meeting_type: str
    meeting_description: Optional[str]
    meeting_location: Optional[str]
    meeting_url: Optional[str]
    
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Availability(AvailabilityInDB):
    pass


class AvailabilitySlot(BaseModel):
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    is_available: bool
