from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.auth import get_password_hash, verify_password, create_access_token, can_create_user, can_assign_role
from datetime import timedelta
from ..core.config import settings


class UserService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_user(db: Session, user_data: UserCreate, creator: User) -> User:
        """Create a new user with role validation."""
        if not can_create_user(creator):
            raise ValueError("Insufficient permissions to create users")
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        if existing_user:
            raise ValueError("User with this email or username already exists")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            timezone=user_data.timezone,
            bio=user_data.bio,
            role="user"  # Default role for new users
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100, current_user: User = None) -> List[User]:
        """Get users with role-based filtering."""
        query = db.query(User)
        
        # If not admin, only show users that the current user can manage
        if current_user and current_user.role != "admin":
            # For team admins, show only users in their teams
            if current_user.role == "user":
                # Get teams where current user is team admin
                from ..models.team import TeamMember
                admin_teams = db.query(TeamMember.team_id).filter(
                    TeamMember.user_id == current_user.id,
                    TeamMember.role == "team_admin",
                    TeamMember.is_active == True
                ).all()
                
                if admin_teams:
                    team_ids = [team.team_id for team in admin_teams]
                    team_members = db.query(TeamMember.user_id).filter(
                        TeamMember.team_id.in_(team_ids),
                        TeamMember.is_active == True
                    ).all()
                    user_ids = [member.user_id for member in team_members]
                    query = query.filter(User.id.in_(user_ids))
                else:
                    # No teams to manage, return empty
                    return []
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate, updater: User) -> Optional[User]:
        """Update user with permission checking."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Check permissions
        if updater.id != user.id and updater.role != "admin":
            # Check if updater is team admin for user's teams
            from ..models.team import TeamMember
            updater_teams = db.query(TeamMember.team_id).filter(
                TeamMember.user_id == updater.id,
                TeamMember.role == "team_admin",
                TeamMember.is_active == True
            ).all()
            
            user_teams = db.query(TeamMember.team_id).filter(
                TeamMember.user_id == user.id,
                TeamMember.is_active == True
            ).all()
            
            updater_team_ids = {team.team_id for team in updater_teams}
            user_team_ids = {team.team_id for team in user_teams}
            
            if not updater_team_ids.intersection(user_team_ids):
                raise ValueError("Insufficient permissions to update this user")
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user_role(db: Session, user_id: int, new_role: str, updater: User) -> Optional[User]:
        """Update user role with permission checking."""
        if not can_assign_role(updater, new_role):
            raise ValueError("Insufficient permissions to assign this role")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Prevent downgrading admin role unless by another admin
        if user.role == "admin" and updater.role != "admin":
            raise ValueError("Only admins can modify admin roles")
        
        user.role = new_role
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int, deleter: User) -> bool:
        """Delete user with permission checking."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Only admins can delete users
        if deleter.role != "admin":
            raise ValueError("Only admins can delete users")
        
        # Prevent self-deletion
        if deleter.id == user.id:
            raise ValueError("Cannot delete your own account")
        
        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def create_access_token_for_user(user: User) -> str:
        """Create access token for user."""
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        return create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

    @staticmethod
    def get_user_stats(db: Session, user_id: int) -> dict:
        """Get user statistics."""
        from ..models.booking import Booking
        from ..models.availability import Availability
        from ..models.team import TeamMember
        
        # Booking stats
        total_bookings = db.query(Booking).filter(
            (Booking.host_id == user_id) | (Booking.guest_id == user_id)
        ).count()
        
        # Availability stats
        total_availabilities = db.query(Availability).filter(
            Availability.user_id == user_id
        ).count()
        
        # Team stats
        team_memberships = db.query(TeamMember).filter(
            TeamMember.user_id == user_id,
            TeamMember.is_active == True
        ).count()
        
        return {
            "total_bookings": total_bookings,
            "total_availabilities": total_availabilities,
            "team_memberships": team_memberships
        }
