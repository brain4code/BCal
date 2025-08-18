from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..core.database import get_db
from ..models.user import User
from ..models.team import Team, TeamMember
from ..models.availability import Availability
from ..models.booking import Booking, BookingStatus
from ..schemas.booking import BookingCreate, TeamBookingCreate
from ..services.assignment import AssignmentService
from ..services.calendar import CalendarService
from ..services.audit import AuditService

router = APIRouter()


@router.get("/teams/{team_id}/availability", tags=["Public Booking"])
def get_team_availability(
    team_id: int,
    date: str,  # YYYY-MM-DD
    db: Session = Depends(get_db)
):
    """
    Get aggregated availability for a team on a specific date.
    This is the customer-facing endpoint that shows all available agents and their slots.
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Get team availability using the assignment service
    availability_slots = AssignmentService.get_team_availability(
        db=db,
        team_id=team_id,
        date=target_date
    )
    
    return {
        "team_id": team_id,
        "team_name": team.name,
        "date": date,
        "available_slots": availability_slots
    }


@router.post("/teams/{team_id}/book", tags=["Public Booking"])
def book_with_team(
    team_id: int,
    booking_data: TeamBookingCreate,
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Book a meeting with intelligent agent assignment from a team.
    """
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Get booking times (already parsed by Pydantic)
    start_time = booking_data.start_time
    end_time = booking_data.end_time
    
    # Use intelligent assignment to find the best agent
    assigned_agent = AssignmentService.assign_agent(
        db=db,
        date=start_time.date(),
        start_time=start_time,
        end_time=end_time,
        team_id=team_id,
        meeting_type=booking_data.meeting_type
    )
    
    if not assigned_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available agents for the selected time slot"
        )
    
    # Check if guest exists (if not, create a temporary guest record)
    guest = db.query(User).filter(User.email == booking_data.guest_email).first()
    if not guest:
        # Create a temporary guest user
        guest = User(
            email=booking_data.guest_email,
            username=f"guest_{booking_data.guest_email.split('@')[0]}",
            full_name=booking_data.guest_name,
            hashed_password="",  # Guest users don't have passwords
            is_active=True
        )
        db.add(guest)
        db.commit()
        db.refresh(guest)
    
    # Check for booking conflicts
    conflicting_booking = db.query(Booking).filter(
        Booking.host_id == assigned_agent.id,
        Booking.start_time < end_time,
        Booking.end_time > start_time,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
    ).first()
    
    if conflicting_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot is already booked"
        )
    
    # Create the booking
    db_booking = Booking(
        host_id=assigned_agent.id,
        guest_id=guest.id,
        title=booking_data.title,
        description=booking_data.description,
        start_time=start_time,
        end_time=end_time,
        guest_email=booking_data.guest_email,
        guest_name=booking_data.guest_name
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    # Generate ICS calendar invite
    ics_content = CalendarService.generate_ics_invite(
        booking=db_booking,
        host=assigned_agent,
        guest=guest,
        description=booking_data.description
    )
    
    # Log the activity
    AuditService.log_booking_activity(
        db=db,
        action="CREATE",
        booking_id=db_booking.id,
        user_id=guest.id,  # Log as guest activity
        new_values={
            "title": booking_data.title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "assigned_agent": assigned_agent.full_name
        },
        request=request
    )
    
    return {
        "booking": {
            "id": db_booking.id,
            "title": db_booking.title,
            "start_time": db_booking.start_time.isoformat(),
            "end_time": db_booking.end_time.isoformat(),
            "status": db_booking.status,
            "assigned_agent": {
                "id": assigned_agent.id,
                "name": assigned_agent.full_name,
                "email": assigned_agent.email
            }
        },
        "ics_calendar": ics_content,
        "message": f"Booking confirmed with {assigned_agent.full_name}"
    }


@router.get("/teams", tags=["Public Booking"])
def get_available_teams(
    db: Session = Depends(get_db)
):
    """
    Get all available teams for booking.
    """
    teams = db.query(Team).filter(Team.is_active == True).all()
    
    team_list = []
    for team in teams:
        # Count active members
        member_count = db.query(TeamMember).filter(
            TeamMember.team_id == team.id,
            TeamMember.is_active == True
        ).count()
        
        team_list.append({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "member_count": member_count
        })
    
    return {"teams": team_list}
