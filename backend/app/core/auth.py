from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from ..models.user import User
from ..models.team import TeamMember
from ..core.database import get_db
from ..core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()

# Role definitions
ROLES = {
    "visitor": 0,  # Can only view public pages
    "user": 1,     # Can create bookings, manage own availability
    "admin": 2     # Super admin - can do everything
}

TEAM_ROLES = {
    "member": 0,      # Regular team member
    "lead": 1,        # Team lead
    "team_admin": 2   # Team administrator
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = verify_token(credentials.credentials)
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: str):
    """Decorator to require a specific user role."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not has_role(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    return role_checker


def require_user_role():
    """Require at least user role (not visitor)."""
    return require_role("user")


def require_admin_role():
    """Require admin role."""
    return require_role("admin")


def has_role(user: User, required_role: str) -> bool:
    """Check if user has the required role."""
    user_role_level = ROLES.get(user.role, 0)
    required_role_level = ROLES.get(required_role, 0)
    return user_role_level >= required_role_level


def is_admin(user: User) -> bool:
    """Check if user is an admin."""
    return user.role == "admin"


def is_user_or_admin(user: User) -> bool:
    """Check if user is at least a user (not visitor)."""
    return user.role in ["user", "admin"]


def get_user_team_role(user_id: int, team_id: int, db: Session) -> Optional[str]:
    """Get user's role in a specific team."""
    team_member = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.team_id == team_id,
        TeamMember.is_active == True
    ).first()
    return team_member.role if team_member else None


def is_team_admin(user_id: int, team_id: int, db: Session) -> bool:
    """Check if user is a team admin for the specified team."""
    team_role = get_user_team_role(user_id, team_id, db)
    return team_role == "team_admin"


def can_manage_team(user: User, team_id: int, db: Session) -> bool:
    """Check if user can manage a specific team."""
    # Super admins can manage all teams
    if is_admin(user):
        return True
    
    # Team admins can manage their own teams
    if is_team_admin(user.id, team_id, db):
        return True
    
    return False


def can_manage_user(manager: User, target_user: User, db: Session) -> bool:
    """Check if manager can manage target user."""
    # Super admins can manage all users
    if is_admin(manager):
        return True
    
    # Users can only manage themselves (for profile updates)
    if manager.id == target_user.id:
        return True
    
    # Team admins can manage users in their teams
    if manager.role == "user":
        # Check if manager is team admin in any team where target_user is a member
        manager_teams = db.query(TeamMember).filter(
            TeamMember.user_id == manager.id,
            TeamMember.role == "team_admin",
            TeamMember.is_active == True
        ).all()
        
        for team_member in manager_teams:
            target_in_team = db.query(TeamMember).filter(
                TeamMember.user_id == target_user.id,
                TeamMember.team_id == team_member.team_id,
                TeamMember.is_active == True
            ).first()
            if target_in_team:
                return True
    
    return False


def can_create_user(creator: User) -> bool:
    """Check if user can create new users."""
    return is_admin(creator) or creator.role == "user"  # Team admins (users) can create team members


def can_assign_role(assigner: User, target_role: str) -> bool:
    """Check if user can assign a specific role."""
    # Only admins can assign admin role
    if target_role == "admin":
        return is_admin(assigner)
    
    # Admins can assign any role
    if is_admin(assigner):
        return True
    
    # Team admins can assign user role (for team members)
    if assigner.role == "user" and target_role == "user":
        return True
    
    return False
