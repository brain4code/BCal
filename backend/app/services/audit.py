from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.audit import AuditLog
from ..schemas.audit import AuditLogCreate
from fastapi import Request


class AuditService:
    @staticmethod
    def log_activity(
        db: Session,
        action: str,
        resource_type: str,
        user_id: Optional[int] = None,
        resource_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Log an activity in the audit system.
        """
        audit_data = AuditLogCreate(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        audit_log = AuditLog(**audit_data.dict())
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def log_user_activity(
        db: Session,
        action: str,
        user_id: int,
        request: Optional[Request] = None
    ):
        """
        Log user-specific activities like login, logout, etc.
        """
        return AuditService.log_activity(
            db=db,
            action=action,
            resource_type="User",
            user_id=user_id,
            request=request
        )

    @staticmethod
    def log_booking_activity(
        db: Session,
        action: str,
        booking_id: int,
        user_id: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Log booking-related activities.
        """
        return AuditService.log_activity(
            db=db,
            action=action,
            resource_type="Booking",
            user_id=user_id,
            resource_id=booking_id,
            old_values=old_values,
            new_values=new_values,
            request=request
        )

    @staticmethod
    def log_availability_activity(
        db: Session,
        action: str,
        availability_id: int,
        user_id: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Log availability-related activities.
        """
        return AuditService.log_activity(
            db=db,
            action=action,
            resource_type="Availability",
            user_id=user_id,
            resource_id=availability_id,
            old_values=old_values,
            new_values=new_values,
            request=request
        )

    @staticmethod
    def log_team_activity(
        db: Session,
        action: str,
        team_id: int,
        user_id: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Log team-related activities.
        """
        return AuditService.log_activity(
            db=db,
            action=action,
            resource_type="Team",
            user_id=user_id,
            resource_id=team_id,
            old_values=old_values,
            new_values=new_values,
            request=request
        )
