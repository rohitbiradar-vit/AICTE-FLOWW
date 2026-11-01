import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: int
    document_uuid: str
    institution_id: int
    application_id: Optional[int] = None
    document_type: str
    title: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    sha256_hash: str
    version: int
    is_current: bool
    issue_date: Optional[datetime.datetime] = None
    expiry_date: Optional[datetime.datetime] = None
    requires_renewal: bool = False
    verification_status: str
    verification_notes: Optional[str] = None
    verified_by_user_id: Optional[int] = None
    verified_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class DocumentVerifyRequest(BaseModel):
    verification_status: str  # VERIFIED, REJECTED, REQUIRES_CLARIFICATION
    verification_notes: Optional[str] = None
    issue_date: Optional[datetime.datetime] = None
    expiry_date: Optional[datetime.datetime] = None
