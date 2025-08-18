from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..models.booking import BookingStatus


class BookingBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    guest_email: EmailStr
    guest_name: str


class BookingCreate(BookingBase):
    host_id: int


class TeamBookingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    guest_name: str
    guest_email: str
    meeting_type: Optional[str] = "general"


class BookingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[BookingStatus] = None


class BookingInDB(BookingBase):
    id: int
    host_id: int
    guest_id: int
    status: BookingStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Booking(BookingInDB):
    host_name: Optional[str] = None
    guest_name: Optional[str] = None


class BookingWithDetails(Booking):
    host: dict
    guest: dict


class DashboardStats(BaseModel):
    total_bookings: int
    pending_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    completed_bookings: int
    total_users: int
    active_users: int
