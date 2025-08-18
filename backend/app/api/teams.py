from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..models.team import Team, TeamMember, Project
from ..schemas.team import (
    Team as TeamSchema,
    TeamCreate,
    TeamUpdate,
    TeamMember as TeamMemberSchema,
    TeamMemberCreate,
    TeamMemberUpdate,
    Project as ProjectSchema,
    ProjectCreate,
    ProjectUpdate,
    TeamWithMembers
)
from ..api.deps import get_current_admin_user
from ..services.audit import AuditService
from fastapi import Request

router = APIRouter()


@router.get("/", response_model=List[TeamSchema], tags=["Teams"])
def get_teams(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all teams (admin only).
    """
    teams = db.query(Team).filter(Team.is_active == True).all()
    return teams


@router.post("/", response_model=TeamSchema, tags=["Teams"])
def create_team(
    team: TeamCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Create a new team (admin only).
    """
    # Check if team name already exists
    existing_team = db.query(Team).filter(Team.name == team.name).first()
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists"
        )
    
    db_team = Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    # Log the activity
    AuditService.log_team_activity(
        db=db,
        action="CREATE",
        team_id=db_team.id,
        user_id=current_user.id,
        new_values=team.dict(),
        request=request
    )
    
    return db_team


@router.get("/{team_id}", response_model=TeamWithMembers, tags=["Teams"])
def get_team(
    team_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific team with members (admin only).
    """
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return team


@router.put("/{team_id}", response_model=TeamSchema, tags=["Teams"])
def update_team(
    team_id: int,
    team_update: TeamUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Update a team (admin only).
    """
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    old_values = {"name": team.name, "description": team.description, "is_active": team.is_active}
    
    update_data = team_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)
    
    db.commit()
    db.refresh(team)
    
    # Log the activity
    AuditService.log_team_activity(
        db=db,
        action="UPDATE",
        team_id=team.id,
        user_id=current_user.id,
        old_values=old_values,
        new_values=update_data,
        request=request
    )
    
    return team


@router.delete("/{team_id}", tags=["Teams"])
def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Delete a team (admin only).
    """
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check if team has members
    member_count = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.is_active == True).count()
    if member_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete team with active members"
        )
    
    team.is_active = False
    db.commit()
    
    # Log the activity
    AuditService.log_team_activity(
        db=db,
        action="DELETE",
        team_id=team.id,
        user_id=current_user.id,
        old_values={"name": team.name, "description": team.description},
        request=request
    )
    
    return {"message": "Team deleted successfully"}


# Team Members endpoints
@router.get("/{team_id}/members", response_model=List[dict], tags=["Team Members"])
def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all members of a team (admin only).
    """
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Get members with user details
    members = db.query(TeamMember, User).join(
        User, TeamMember.user_id == User.id
    ).filter(
        TeamMember.team_id == team_id,
        TeamMember.is_active == True
    ).all()
    
    result = []
    for member, user in members:
        result.append({
            "id": member.id,
            "team_id": member.team_id,
            "user_id": member.user_id,
            "role": member.role,
            "is_active": member.is_active,
            "joined_at": member.joined_at,
            "updated_at": member.updated_at,
            "user_name": user.full_name,
            "user_email": user.email
        })
    
    return result


@router.post("/{team_id}/members", response_model=TeamMemberSchema, tags=["Team Members"])
def add_team_member(
    team_id: int,
    member: TeamMemberCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Add a member to a team (admin only).
    """
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == member.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already a member
    existing_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == member.user_id,
        TeamMember.is_active == True
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team"
        )
    
    db_member = TeamMember(**member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    return db_member


@router.put("/{team_id}/members/{member_id}", response_model=TeamMemberSchema, tags=["Team Members"])
def update_team_member(
    team_id: int,
    member_id: int,
    member_update: TeamMemberUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Update a team member (admin only).
    """
    member = db.query(TeamMember).filter(
        TeamMember.id == member_id,
        TeamMember.team_id == team_id,
        TeamMember.is_active == True
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    old_values = {"role": member.role, "is_active": member.is_active}
    
    update_data = member_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)
    
    db.commit()
    db.refresh(member)
    
    return member


@router.delete("/{team_id}/members/{member_id}", tags=["Team Members"])
def remove_team_member(
    team_id: int,
    member_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Remove a member from a team (admin only).
    """
    member = db.query(TeamMember).filter(
        TeamMember.id == member_id,
        TeamMember.team_id == team_id,
        TeamMember.is_active == True
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    member.is_active = False
    db.commit()
    
    return {"message": "Team member removed successfully"}


# Projects endpoints
@router.post("/{team_id}/projects", response_model=ProjectSchema, tags=["Projects"])
def create_project(
    team_id: int,
    project: ProjectCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Create a new project for a team (admin only).
    """
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project


@router.get("/{team_id}/projects", response_model=List[ProjectSchema], tags=["Projects"])
def get_team_projects(
    team_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all projects for a team (admin only).
    """
    projects = db.query(Project).filter(
        Project.team_id == team_id,
        Project.is_active == True
    ).all()
    
    return projects
