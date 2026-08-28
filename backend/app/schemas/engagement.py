from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    entity_type: str  # problem|solution|collaboration
    entity_id: str
    content: str = Field(min_length=1)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    entity_id: str
    user_id: str
    content: str
    created_at: datetime


class UpvoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    problem_id: str
    user_id: str
    created_at: datetime


class CitizenProfileUpdate(BaseModel):
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None


class CitizenProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
