from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from ..models.user import User
from ..models.availability import Availability
from ..models.booking import Booking, BookingStatus
from ..models.team import Team, TeamMember


class AssignmentService:
    @staticmethod
    def get_available_agents(
        db: Session,
        date: datetime,
        start_time: datetime,
        end_time: datetime,
        team_id: Optional[int] = None,
        meeting_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all available agents for a given time slot with load balancing.
        """
        # Get the day of week (0=Monday, 6=Sunday)
        day_of_week = date.weekday()
        
        # Base query for users with availability
        query = db.query(User).join(Availability).filter(
            User.is_active == True,
            Availability.day_of_week == day_of_week,
            Availability.is_active == True,
            Availability.start_time <= start_time.strftime("%H:%M"),
            Availability.end_time >= end_time.strftime("%H:%M")
        )
        
        # Filter by team if specified
        if team_id:
            query = query.join(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.is_active == True)
        
        # Filter by meeting type if specified
        if meeting_type:
            query = query.filter(Availability.meeting_type == meeting_type)
        
        available_agents = query.all()
        
        # Check for booking conflicts and calculate load
        agents_with_load = []
        for agent in available_agents:
            # Check for conflicts
            conflicting_bookings = db.query(Booking).filter(
                Booking.host_id == agent.id,
                Booking.start_time < end_time,
                Booking.end_time > start_time,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            ).count()
            
            if conflicting_bookings == 0:
                # Calculate current load (bookings today)
                today_start = datetime.combine(date, datetime.min.time())
                today_end = today_start + timedelta(days=1)
                
                today_bookings = db.query(Booking).filter(
                    Booking.host_id == agent.id,
                    Booking.start_time >= today_start,
                    Booking.start_time < today_end,
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
                ).count()
                
                # Get agent's availability settings
                availability = db.query(Availability).filter(
                    Availability.user_id == agent.id,
                    Availability.day_of_week == day_of_week,
                    Availability.is_active == True
                ).first()
                
                agents_with_load.append({
                    "agent": agent,
                    "load": today_bookings,
                    "availability": availability,
                    "priority_score": AssignmentService._calculate_priority_score(
                        today_bookings, availability, agent
                    )
                })
        
        # Sort by priority score (lower load = higher priority)
        agents_with_load.sort(key=lambda x: x["priority_score"])
        
        return agents_with_load

    @staticmethod
    def assign_agent(
        db: Session,
        date: datetime,
        start_time: datetime,
        end_time: datetime,
        team_id: Optional[int] = None,
        meeting_type: Optional[str] = None,
        preferred_agent_id: Optional[int] = None
    ) -> Optional[User]:
        """
        Intelligently assign an agent based on availability and load balancing.
        """
        available_agents = AssignmentService.get_available_agents(
            db, date, start_time, end_time, team_id, meeting_type
        )
        
        if not available_agents:
            return None
        
        # If preferred agent is available and has reasonable load, assign them
        if preferred_agent_id:
            for agent_data in available_agents:
                if agent_data["agent"].id == preferred_agent_id and agent_data["load"] < 5:
                    return agent_data["agent"]
        
        # Otherwise, assign the agent with the lowest load
        return available_agents[0]["agent"]

    @staticmethod
    def get_team_availability(
        db: Session,
        team_id: int,
        date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated availability for a team on a specific date.
        """
        day_of_week = date.weekday()
        
        # Get team members with their availability
        team_members = db.query(User, Availability).join(
            TeamMember
        ).join(
            Availability
        ).filter(
            TeamMember.team_id == team_id,
            TeamMember.is_active == True,
            User.is_active == True,
            Availability.day_of_week == day_of_week,
            Availability.is_active == True
        ).all()
        
        availability_slots = []
        
        for user, availability in team_members:
            # Generate time slots for this user
            start_hour, start_minute = map(int, availability.start_time.split(":"))
            end_hour, end_minute = map(int, availability.end_time.split(":"))
            
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            
            # Check for existing bookings
            today_start = datetime.combine(date, datetime.min.time())
            today_end = datetime.combine(date, datetime.max.time())
            existing_bookings = db.query(Booking).filter(
                Booking.host_id == user.id,
                Booking.start_time >= today_start,
                Booking.start_time < today_end,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            ).all()
            
            current_minutes = start_minutes
            while current_minutes + 30 <= end_minutes:
                slot_start = datetime.combine(date, datetime.min.time()) + timedelta(minutes=current_minutes)
                slot_end = slot_start + timedelta(minutes=30)
                
                # Check if slot conflicts with existing bookings
                is_available = True
                for booking in existing_bookings:
                    if (slot_start < booking.end_time and slot_end > booking.start_time):
                        is_available = False
                        break
                
                if is_available:
                    availability_slots.append({
                        "user_id": user.id,
                        "user_name": user.full_name,
                        "user_email": user.email,
                        "start_time": slot_start.strftime("%H:%M"),
                        "end_time": slot_end.strftime("%H:%M"),
                        "meeting_type": availability.meeting_type,
                        "meeting_description": availability.meeting_description,
                        "meeting_location": availability.meeting_location,
                        "slot_duration": availability.slot_duration_minutes or 30
                    })
                
                current_minutes += 30
        
        return availability_slots

    @staticmethod
    def _calculate_priority_score(
        current_load: int,
        availability: Availability,
        agent: User
    ) -> float:
        """
        Calculate priority score for agent assignment.
        Lower score = higher priority.
        """
        # Base score is the current load
        score = current_load
        
        # Bonus for agents with longer availability windows
        if availability:
            start_hour, start_minute = map(int, availability.start_time.split(":"))
            end_hour, end_minute = map(int, availability.end_time.split(":"))
            availability_hours = (end_hour * 60 + end_minute - start_hour * 60 - start_minute) / 60
            score -= availability_hours * 0.1  # Bonus for longer availability
        
        # Bonus for agents with specific meeting types
        if availability and availability.meeting_type and availability.meeting_type != "general":
            score -= 0.5
        
        # Bonus for agents with lower historical load (if we had that data)
        # For now, we'll use a simple heuristic
        
        return score
