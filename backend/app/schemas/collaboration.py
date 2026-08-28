from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class CollaborationCreate(BaseModel):
    proposal_id: str
    industry_id: str
    notes: Optional[str] = None
    stage: str = "interested"  # interested|funding|prototype|pilot|implementation|impact_logged


class CollaborationUpdate(BaseModel):
    stage: Optional[str] = None
    notes: Optional[str] = None


class CollaborationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    proposal_id: str
    industry_id: str
    stage: str
    notes: Optional[str] = None
    started_at: datetime
    updated_at: datetime


class MilestoneCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "pending"  # pending|in_progress|completed|delayed


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    completed_at: Optional[datetime] = None


class MilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    collaboration_id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    created_at: datetime


class DeliverableIn(BaseModel):
    file_url: Optional[str] = None
    description: Optional[str] = None


class DeliverableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    milestone_id: str
    file_url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


class IPRecordIn(BaseModel):
    type: Optional[str] = None
    status: Optional[str] = None
    reference_no: Optional[str] = None


class IPRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    collaboration_id: str
    type: Optional[str] = None
    status: Optional[str] = None
    reference_no: Optional[str] = None
    created_at: datetime


class ImpactReportIn(BaseModel):
    beneficiaries_count: Optional[int] = None
    impact_summary: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None


class ImpactReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    collaboration_id: str
    beneficiaries_count: Optional[int] = None
    impact_summary: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    reported_at: datetime
