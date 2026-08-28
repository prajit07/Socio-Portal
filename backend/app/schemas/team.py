from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class TeamCreate(BaseModel):
    problem_id: str
    name: str
    university_id: Optional[str] = None
    member_ids: Optional[List[str]] = None  # user ids to add as members


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    problem_id: str
    university_id: Optional[str] = None
    name: str
    created_by: str
    created_at: datetime


class AddMemberIn(BaseModel):
    user_id: str
    role: Optional[str] = None


class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    team_id: str
    user_id: str
    role: Optional[str] = None
    created_at: datetime
