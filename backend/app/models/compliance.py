import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class UndertakingStatus:
    PENDING_SUBMISSION = "PENDING_SUBMISSION"
    SUBMITTED = "SUBMITTED"
    UNDER_VERIFICATION = "UNDER_VERIFICATION"
    CORRECTION_REQUESTED = "CORRECTION_REQUESTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    OVERDUE = "OVERDUE"

class Undertaking(Base):
    __tablename__ = "undertakings"

    id = Column(Integer, primary_key=True, index=True)
    undertaking_code = Column(String(50), unique=True, index=True, nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False)
    requirement_clause = Column(String(255), nullable=False) # e.g. "AICTE APH 2026 Ch. 3 Cl. 7 - Barrier-Free Environment"
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=False, index=True)
    
    status = Column(String(50), default=UndertakingStatus.PENDING_SUBMISSION, nullable=False, index=True)
    
    # Evidence Submission
    evidence_filename = Column(String(255), nullable=True)
    evidence_file_path = Column(Text, nullable=True)
    evidence_description = Column(Text, nullable=True)
    submission_version = Column(Integer, default=0)
    submitted_at = Column(DateTime, nullable=True)
    
    # Verification
    verified_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verification_notes = Column(Text, nullable=True)
    correction_reason = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Renewal or Follow-up
    requires_annual_renewal = Column(Boolean, default=False)
    renewal_due_date = Column(DateTime, nullable=True)
    
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    institution = relationship("Institution", back_populates="undertakings")
    application = relationship("Application", back_populates="undertakings")
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
