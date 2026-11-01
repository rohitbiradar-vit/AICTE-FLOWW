import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class ScrutinyReportResponse(BaseModel):
    id: int
    application_id: int
    report_version: int
    priority_score: int
    priority_band: str
    score_formula_breakdown: Dict[str, Any]
    document_inventory: List[Dict[str, Any]]
    extracted_summary: Dict[str, Any]
    missing_evidence: List[Dict[str, Any]]
    inconsistencies: List[Dict[str, Any]]
    expiry_findings: List[Dict[str, Any]]
    low_confidence_extractions: List[Dict[str, Any]]
    findings_requiring_human_review: List[Dict[str, Any]]
    rules_checked: List[Dict[str, Any]]
    suggested_actions: List[str]
    reviewer_decision: str
    reviewer_notes: Optional[str] = None
    reviewed_by_user_id: Optional[int] = None
    reviewed_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class ScrutinyReviewRequest(BaseModel):
    decision: str  # AGREED, OVERRIDDEN, RETURN_FOR_CLARIFICATION
    notes: Optional[str] = None
