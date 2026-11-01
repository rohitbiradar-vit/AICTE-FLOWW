import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class ApplicationCreate(BaseModel):
    academic_year: str = "2026-2027"
    application_type: str = "EXTENSION_OF_APPROVAL"
    declared_land_acres: Optional[str] = "5.0"
    declared_builtup_sqm: Optional[str] = "8500"
    declared_intake: Optional[int] = 480
    declared_faculty_count: Optional[int] = 45
    application_data: Optional[Dict[str, Any]] = None

class ApplicationUpdate(BaseModel):
    declared_land_acres: Optional[str] = None
    declared_builtup_sqm: Optional[str] = None
    declared_intake: Optional[int] = None
    declared_faculty_count: Optional[int] = None
    application_data: Optional[Dict[str, Any]] = None

class TransitionRequest(BaseModel):
    target_stage_key: str
    reason: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class ClockPauseRequest(BaseModel):
    reason: str
    authorized_clause: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: int
    application_number: str
    institution_id: int
    institution_name: Optional[str] = None
    academic_year: str
    application_type: str
    current_stage_key: str
    workflow_code: str
    assigned_official_id: Optional[int] = None
    assigned_official_name: Optional[str] = None
    declared_land_acres: Optional[str] = None
    declared_builtup_sqm: Optional[str] = None
    declared_intake: Optional[int] = None
    declared_faculty_count: Optional[int] = None
    application_data: Optional[Dict[str, Any]] = None
    clarification_notes: Optional[str] = None
    resubmission_count: int = 0
    current_deadline: Optional[datetime.datetime] = None
    status: str
    submitted_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
