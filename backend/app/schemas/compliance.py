import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class UndertakingCreate(BaseModel):
    institution_id: int
    application_id: Optional[int] = None
    title: str
    requirement_clause: str
    description: str
    due_date: datetime.datetime
    requires_annual_renewal: bool = False

class UndertakingVerifyRequest(BaseModel):
    decision: str  # ACCEPTED, CORRECTION_REQUESTED, REJECTED
    notes: Optional[str] = None
    correction_reason: Optional[str] = None

class UndertakingResponse(BaseModel):
    id: int
    undertaking_code: str
    institution_id: int
    application_id: Optional[int] = None
    title: str
    requirement_clause: str
    description: str
    due_date: datetime.datetime
    status: str
    evidence_filename: Optional[str] = None
    evidence_description: Optional[str] = None
    submission_version: int = 0
    submitted_at: Optional[datetime.datetime] = None
    verified_by_user_id: Optional[int] = None
    verification_notes: Optional[str] = None
    correction_reason: Optional[str] = None
    verified_at: Optional[datetime.datetime] = None
    requires_annual_renewal: bool = False
    renewal_due_date: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
