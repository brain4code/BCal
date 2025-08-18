from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..models.availability import Availability
from ..models.booking import Booking
from ..schemas.availability import (
    Availability as AvailabilitySchema,
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilitySlot
)
from ..api.deps import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[AvailabilitySchema], tags=["Availability"])
def get_user_availability(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's availability settings.
    """
    availabilities = db.query(Availability).filter(
        Availability.user_id == current_user.id,
        Availability.is_active == True
    ).all()
    return availabilities


@router.post("/", response_model=AvailabilitySchema, tags=["Availability"])
def create_availability(
    availability: AvailabilityCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new availability slot for the current user.
    """
    # Validate time format and logic
    try:
        start_hour, start_minute = map(int, availability.start_time.split(":"))
        end_hour, end_minute = map(int, availability.end_time.split(":"))
        
        if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59):
            raise ValueError("Invalid start time")
        if not (0 <= end_hour <= 23 and 0 <= end_minute <= 59):
            raise ValueError("Invalid end time")
        
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute
        
        if start_minutes >= end_minutes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time format. Use HH:MM"
        )
    
    # Check if availability already exists for this day and time
    existing = db.query(Availability).filter(
        Availability.user_id == current_user.id,
        Availability.day_of_week == availability.day_of_week,
        Availability.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Availability already exists for this day"
        )
    
    db_availability = Availability(
        user_id=current_user.id,
        day_of_week=availability.day_of_week,
        start_time=availability.start_time,
        end_time=availability.end_time
    )
    db.add(db_availability)
    db.commit()
    db.refresh(db_availability)
    
    return db_availability


@router.put("/{availability_id}", response_model=AvailabilitySchema, tags=["Availability"])
def update_availability(
    availability_id: int,
    availability: AvailabilityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an availability slot.
    """
    db_availability = db.query(Availability).filter(
        Availability.id == availability_id,
        Availability.user_id == current_user.id
    ).first()
    
    if not db_availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found"
        )
    
    update_data = availability.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_availability, field, value)
    
    db.commit()
    db.refresh(db_availability)
    
    return db_availability


@router.delete("/{availability_id}", tags=["Availability"])
def delete_availability(
    availability_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an availability slot.
    """
    db_availability = db.query(Availability).filter(
        Availability.id == availability_id,
        Availability.user_id == current_user.id
    ).first()
    
    if not db_availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found"
        )
    
    db.delete(db_availability)
    db.commit()
    
    return {"message": "Availability deleted successfully"}


@router.get("/slots/{user_id}", response_model=List[AvailabilitySlot], tags=["Availability"])
def get_available_slots(
    user_id: int,
    date: str,  # YYYY-MM-DD
    db: Session = Depends(get_db)
):
    """
    Get available time slots for a specific user on a specific date.
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Get user's availability for the day of week
    day_of_week = target_date.weekday()
    availabilities = db.query(Availability).filter(
        Availability.user_id == user_id,
        Availability.day_of_week == day_of_week,
        Availability.is_active == True
    ).all()
    
    # Get existing bookings for the date
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)
    
    existing_bookings = db.query(Booking).filter(
        Booking.host_id == user_id,
        Booking.start_time >= start_of_day,
        Booking.start_time < end_of_day,
        Booking.status.in_(["pending", "confirmed"])
    ).all()
    
    slots = []
    for availability in availabilities:
        # Generate 30-minute slots within the availability window
        start_hour, start_minute = map(int, availability.start_time.split(":"))
        end_hour, end_minute = map(int, availability.end_time.split(":"))
        
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute
        
        current_minutes = start_minutes
        while current_minutes + 30 <= end_minutes:
            slot_start = datetime.combine(target_date, datetime.min.time()) + timedelta(minutes=current_minutes)
            slot_end = slot_start + timedelta(minutes=30)
            
            # Check if slot conflicts with existing bookings
            is_available = True
            for booking in existing_bookings:
                if (slot_start < booking.end_time and slot_end > booking.start_time):
                    is_available = False
                    break
            
            slots.append(AvailabilitySlot(
                date=date,
                start_time=f"{current_minutes // 60:02d}:{current_minutes % 60:02d}",
                end_time=f"{(current_minutes + 30) // 60:02d}:{(current_minutes + 30) % 60:02d}",
                is_available=is_available
            ))
            
            current_minutes += 30
    
    return slots
