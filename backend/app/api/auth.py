from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.auth import verify_password, get_password_hash, create_access_token, require_admin_role
from ..models.user import User
from ..schemas.user import UserCreate, Token, User as UserSchema
from ..api.deps import get_current_user
from ..services.user import UserService

router = APIRouter()


@router.post("/users", response_model=UserSchema, tags=["Authentication"])
def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role())
):
    """
    Create a new user (Admin only).
    """
    try:
        return UserService.create_user(db, user, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token, tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login to get access token.
    """
    user = UserService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = UserService.create_access_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema, tags=["Authentication"])
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    """
    return current_user
