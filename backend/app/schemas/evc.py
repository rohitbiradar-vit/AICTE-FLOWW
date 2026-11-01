import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class EVCVisitCreate(BaseModel):
    application_id: int
    proposed_date: datetime.datetime
    assigned_officers: List[Dict[str, Any]]

class EVCReportSubmit(BaseModel):
    visit_outcome: str  # RECOMMENDED, DEFICIENCIES_NOTED, REJECTED
    report_summary: str
    deficiencies_found: List[str] = []
    follow_up_required: bool = False

class EVCVisitResponse(BaseModel):
    id: int
    visit_reference: str
    application_id: int
    institution_id: int
    application_number: Optional[str] = None
    institution_name: Optional[str] = None
    proposed_date: datetime.datetime
    confirmed_date: Optional[datetime.datetime] = None
    status: str
    assigned_officers: List[Dict[str, Any]]
    preparation_checklist: List[Dict[str, Any]]
    visit_outcome: Optional[str] = None
    report_filename: Optional[str] = None
    report_summary: Optional[str] = None
    deficiencies_found: List[str] = []
    follow_up_required: bool = False
    follow_up_deadline: Optional[datetime.datetime] = None
    conducted_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
