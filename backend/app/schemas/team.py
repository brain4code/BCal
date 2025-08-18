from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TeamInDB(TeamBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Team(TeamInDB):
    pass


class TeamMemberBase(BaseModel):
    team_id: int
    user_id: int
    role: str = "member"


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMemberUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class TeamMemberInDB(TeamMemberBase):
    id: int
    is_active: bool
    joined_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamMember(TeamMemberInDB):
    pass


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    team_id: int


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectInDB(ProjectBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Project(ProjectInDB):
    pass


class TeamWithMembers(Team):
    members: List[TeamMember] = []
    projects: List[Project] = []
