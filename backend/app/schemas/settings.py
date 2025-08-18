from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemSettingsBase(BaseModel):
    key: str
    value: Optional[str] = None
    value_type: str = "string"
    description: Optional[str] = None


class SystemSettingsCreate(SystemSettingsBase):
    pass


class SystemSettingsUpdate(BaseModel):
    value: Optional[str] = None
    value_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SystemSettingsInDB(SystemSettingsBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemSettings(SystemSettingsInDB):
    pass


class MeetingDefaultsBase(BaseModel):
    name: str
    default_duration_minutes: int = 30
    buffer_before_minutes: int = 0
    buffer_after_minutes: int = 0
    min_notice_hours: int = 2
    max_booking_days: int = 90
    meeting_type: str = "general"
    meeting_description: Optional[str] = None
    meeting_location: Optional[str] = None


class MeetingDefaultsCreate(MeetingDefaultsBase):
    pass


class MeetingDefaultsUpdate(BaseModel):
    name: Optional[str] = None
    default_duration_minutes: Optional[int] = None
    buffer_before_minutes: Optional[int] = None
    buffer_after_minutes: Optional[int] = None
    min_notice_hours: Optional[int] = None
    max_booking_days: Optional[int] = None
    meeting_type: Optional[str] = None
    meeting_description: Optional[str] = None
    meeting_location: Optional[str] = None
    is_active: Optional[bool] = None


class MeetingDefaultsInDB(MeetingDefaultsBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MeetingDefaults(MeetingDefaultsInDB):
    pass
