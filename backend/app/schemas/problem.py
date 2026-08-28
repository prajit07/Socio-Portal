from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import (
    RoleEnum,
    ProblemStatusEnum,
    ProblemPriorityEnum,
    SolutionStatusEnum,
)


# ==================== Problem Schemas ====================

class ProblemBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    evidence_urls: Optional[List[str]] = None
    evidence_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    tags: Optional[List[str]] = None


class ProblemCreate(ProblemBase):
    pass


class ProblemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1)
    evidence_urls: Optional[List[str]] = None
    evidence_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[ProblemStatusEnum] = None
    ai_tags: Optional[List[str]] = None
    ai_category: Optional[str] = None
    ai_priority: Optional[ProblemPriorityEnum] = None
    ai_duplicate_check: Optional[bool] = None
    ai_duplicate_of: Optional[str] = None
    assigned_to_id: Optional[str] = None


class ProblemOut(ProblemBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: ProblemStatusEnum
    ai_tags: Optional[List[str]] = None
    ai_category: Optional[str] = None
    ai_priority: Optional[ProblemPriorityEnum] = None
    ai_duplicate_check: Optional[bool] = None
    ai_duplicate_of: Optional[str] = None
    assigned_to_id: Optional[str] = None
    submitter_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    deletion_reason: Optional[str] = None


class ProblemListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    status: ProblemStatusEnum
    ai_category: Optional[str] = None
    ai_priority: Optional[ProblemPriorityEnum] = None
    submitter_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    deleted_at: Optional[datetime] = None


class ProblemDelete(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


# ==================== Solution Schemas ====================

class SolutionBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    approach: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    estimated_timeline: Optional[str] = None
    estimated_budget: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    document_urls: Optional[List[str]] = None


class SolutionCreate(SolutionBase):
    pass


class SolutionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1)
    approach: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    estimated_timeline: Optional[str] = None
    estimated_budget: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    document_urls: Optional[List[str]] = None
    status: Optional[SolutionStatusEnum] = None


class SolutionOut(SolutionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: SolutionStatusEnum
    problem_id: str
    author_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SolutionListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: SolutionStatusEnum
    problem_id: str
    author_id: Optional[str] = None
    created_at: datetime


# ==================== User Schemas (Extended) ====================

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    role: RoleEnum
    phone: Optional[str] = None
    domain_tags: Optional[List[str]] = None


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=32)
    domain_tags: Optional[List[str]] = None