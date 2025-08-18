from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from datetime import datetime, date
from ..core.database import get_db
from ..models.user import User
from ..models.booking import Booking, BookingStatus
from ..schemas.user import User as UserSchema
from ..schemas.booking import BookingWithDetails, DashboardStats, BookingUpdate
from ..api.deps import get_current_admin_user

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats, tags=["Admin"])
def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics for admin.
    """
    total_bookings = db.query(Booking).count()
    pending_bookings = db.query(Booking).filter(Booking.status == BookingStatus.PENDING).count()
    confirmed_bookings = db.query(Booking).filter(Booking.status == BookingStatus.CONFIRMED).count()
    cancelled_bookings = db.query(Booking).filter(Booking.status == BookingStatus.CANCELLED).count()
    completed_bookings = db.query(Booking).filter(Booking.status == BookingStatus.COMPLETED).count()
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    return DashboardStats(
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        confirmed_bookings=confirmed_bookings,
        cancelled_bookings=cancelled_bookings,
        completed_bookings=completed_bookings,
        total_users=total_users,
        active_users=active_users
    )


@router.get("/users", response_model=List[UserSchema], tags=["Admin"])
def get_all_users(
    search: Optional[str] = Query(None, description="Search by name, email, or username"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all users with optional filtering (admin only).
    """
    query = db.query(User)
    
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%")
            )
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)
    
    users = query.order_by(User.created_at.desc()).all()
    return users


@router.get("/bookings", response_model=List[BookingWithDetails], tags=["Admin"])
def get_all_bookings(
    search: Optional[str] = Query(None, description="Search by title or guest name"),
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    host_id: Optional[int] = Query(None, description="Filter by host ID"),
    guest_id: Optional[int] = Query(None, description="Filter by guest ID"),
    start_date: Optional[date] = Query(None, description="Filter bookings from this date"),
    end_date: Optional[date] = Query(None, description="Filter bookings until this date"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all bookings with comprehensive filtering (admin only).
    """
    query = db.query(Booking)
    
    if search:
        query = query.filter(
            or_(
                Booking.title.ilike(f"%{search}%"),
                Booking.description.ilike(f"%{search}%")
            )
        )
    
    if status:
        query = query.filter(Booking.status == status)
    
    if host_id:
        query = query.filter(Booking.host_id == host_id)
    
    if guest_id:
        query = query.filter(Booking.guest_id == guest_id)
    
    if start_date:
        query = query.filter(Booking.start_time >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.filter(Booking.start_time <= datetime.combine(end_date, datetime.max.time()))
    
    bookings = query.order_by(Booking.start_time.desc()).all()
    
    booking_details = []
    for booking in bookings:
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
        booking_details.append(booking_with_details)
    
    return booking_details


@router.put("/bookings/{booking_id}/status", response_model=BookingWithDetails, tags=["Admin"])
def update_booking_status(
    booking_id: int,
    status_update: BookingUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update booking status (admin only).
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    if status_update.status:
        booking.status = status_update.status
    
    if status_update.title:
        booking.title = status_update.title
    
    if status_update.description:
        booking.description = status_update.description
    
    db.commit()
    db.refresh(booking)
    
    # Get updated booking with details
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


@router.delete("/bookings/{booking_id}", tags=["Admin"])
def delete_booking(
    booking_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a booking (admin only).
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    db.delete(booking)
    db.commit()
    
    return {"message": "Booking deleted successfully"}


@router.put("/users/{user_id}/toggle-admin", response_model=UserSchema, tags=["Admin"])
def toggle_admin_status(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Toggle admin status for a user (admin only).
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own admin status"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Toggle between admin and user
    user.role = 'user' if user.role == 'admin' else 'admin'
    db.commit()
    db.refresh(user)
    
    return user


@router.put("/users/{user_id}/toggle-active", response_model=UserSchema, tags=["Admin"])
def toggle_user_active_status(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Toggle active status for a user (admin only).
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own active status"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    return user


@router.put("/users/{user_id}/role", response_model=UserSchema, tags=["Admin"])
def update_user_role(
    user_id: int,
    role_update: dict,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user role (admin only).
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own role"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_role = role_update.get('role')
    if new_role not in ['visitor', 'user', 'team_admin', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be one of: visitor, user, team_admin, admin"
        )
    
    user.role = new_role
    db.commit()
    db.refresh(user)
    
    return user
