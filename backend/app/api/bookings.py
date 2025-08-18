from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..models.booking import Booking, BookingStatus
from ..schemas.booking import (
    Booking as BookingSchema,
    BookingCreate,
    BookingUpdate,
    BookingWithDetails
)
from ..api.deps import get_current_active_user

router = APIRouter()


@router.post("/", response_model=BookingSchema, tags=["Bookings"])
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new booking.
    """
    # Check if host exists
    host = db.query(User).filter(User.id == booking.host_id).first()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found"
        )
    
    # Check if guest exists (if not, create a temporary guest record)
    guest = db.query(User).filter(User.email == booking.guest_email).first()
    if not guest:
        # Create a temporary guest user
        guest = User(
            email=booking.guest_email,
            username=f"guest_{booking.guest_email.split('@')[0]}",
            full_name=booking.guest_name,
            hashed_password="",  # Guest users don't have passwords
            is_active=True
        )
        db.add(guest)
        db.commit()
        db.refresh(guest)
    
    # Check for booking conflicts
    conflicting_booking = db.query(Booking).filter(
        Booking.host_id == booking.host_id,
        Booking.start_time < booking.end_time,
        Booking.end_time > booking.start_time,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
    ).first()
    
    if conflicting_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot is already booked"
        )
    
    db_booking = Booking(
        host_id=booking.host_id,
        guest_id=guest.id,
        title=booking.title,
        description=booking.description,
        start_time=booking.start_time,
        end_time=booking.end_time,
        guest_email=booking.guest_email,
        guest_name=booking.guest_name
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    return db_booking


@router.get("/", response_model=List[BookingWithDetails], tags=["Bookings"])
def get_user_bookings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's bookings (both as host and guest).
    """
    # Get bookings where user is host
    host_bookings = db.query(Booking).filter(
        Booking.host_id == current_user.id
    ).all()
    
    # Get bookings where user is guest
    guest_bookings = db.query(Booking).filter(
        Booking.guest_id == current_user.id
    ).all()
    
    # Combine and format bookings
    all_bookings = []
    for booking in host_bookings + guest_bookings:
        host = db.query(User).filter(User.id == booking.host_id).first()
        guest = db.query(User).filter(User.id == booking.guest_id).first()
        
        booking_with_details = BookingWithDetails(
            **booking.__dict__,
            host={
                "id": host.id,
                "full_name": host.full_name,
                "email": host.email
            },
            guest={
                "id": guest.id,
                "full_name": guest.full_name,
                "email": guest.email
            }
        )
        all_bookings.append(booking_with_details)
    
    return all_bookings


@router.get("/{booking_id}", response_model=BookingWithDetails, tags=["Bookings"])
def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific booking by ID.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if user has access to this booking
    if booking.host_id != current_user.id and booking.guest_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking"
        )
    
    host = db.query(User).filter(User.id == booking.host_id).first()
    guest = db.query(User).filter(User.id == booking.guest_id).first()
    
    return BookingWithDetails(
        **booking.__dict__,
        host={
            "id": host.id,
            "full_name": host.full_name,
            "email": host.email
        },
        guest={
            "id": guest.id,
            "full_name": guest.full_name,
            "email": guest.email
        }
    )


@router.put("/{booking_id}", response_model=BookingSchema, tags=["Bookings"])
def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a booking (only host can update).
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Only host can update booking
    if booking.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only host can update booking"
        )
    
    update_data = booking_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    
    return booking


@router.delete("/{booking_id}", tags=["Bookings"])
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a booking.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if user can cancel this booking
    if booking.host_id != current_user.id and booking.guest_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this booking"
        )
    
    booking.status = BookingStatus.CANCELLED
    db.commit()
    
    return {"message": "Booking cancelled successfully"}
