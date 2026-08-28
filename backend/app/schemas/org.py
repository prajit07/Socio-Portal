from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class UniversityCreate(BaseModel):
    name: str
    registration_no: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None


class UniversityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    registration_no: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    verified: bool
    created_at: datetime


class UniversityMemberCreate(BaseModel):
    user_id: str
    member_role: str = "student"  # student|faculty_mentor|admin


class IndustryCreate(BaseModel):
    name: str
    type: Optional[str] = None
    registration_no: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    domain_tags: Optional[List[str]] = None


class IndustryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: Optional[str] = None
    registration_no: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    domain_tags: Optional[List[str]] = None
    verified: bool
    created_at: datetime
