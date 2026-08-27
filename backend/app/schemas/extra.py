from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.models.enums import EvidenceTypeEnum, NotificationTypeEnum, RoutingTypeEnum


# Evidence
class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    problem_id: str
    type: EvidenceTypeEnum
    file_url: Optional[str] = None
    transcript: Optional[str] = None
    created_at: datetime


# Notifications
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationTypeEnum
    message: str
    reference_id: Optional[str] = None
    is_read: bool
    created_at: datetime


# AI Analysis
class AnalysisTag(BaseModel):
    id: str
    name: str
    confidence: float


class AnalysisOut(BaseModel):
    problem_id: str
    category_id: str
    category_name: str
    tags: List[AnalysisTag]
    priority: str
    duplicates: List[dict]
    routed_count: int
    status: str


# Routing preview
class RoutingPreviewOut(BaseModel):
    universities: List[dict]
    industries: List[dict]


# Tags taxonomy
class TagOut(BaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None
    description: Optional[str] = None
