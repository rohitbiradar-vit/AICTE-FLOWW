import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class EVCStatus:
    REQUESTED = "REQUESTED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    REPORT_SUBMITTED = "REPORT_SUBMITTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class EVCVisit(Base):
    __tablename__ = "evc_visits"

    id = Column(Integer, primary_key=True, index=True)
    visit_reference = Column(String(50), unique=True, index=True, nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    proposed_date = Column(DateTime, nullable=False)
    confirmed_date = Column(DateTime, nullable=True)
    status = Column(String(50), default=EVCStatus.REQUESTED, nullable=False, index=True)
    
    # Assignments & Committee
    assigned_officers = Column(JSON, default=list) # List of officer names, designations, emails
    coordinator_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Checklists & Preparation
    preparation_checklist = Column(JSON, default=list) # e.g. [{"item": "Physical Land Verification", "done": true}]
    infrastructure_readiness = Column(String(100), default="PENDING_VERIFICATION")
    
    # Visit Outcome & Report
    visit_outcome = Column(String(100), nullable=True) # RECOMMENDED, DEFICIENCIES_NOTED, REJECTED
    report_filename = Column(String(255), nullable=True)
    report_file_path = Column(Text, nullable=True)
    report_summary = Column(Text, nullable=True)
    deficiencies_found = Column(JSON, default=list)
    follow_up_required = Column(Boolean, default=False)
    follow_up_deadline = Column(DateTime, nullable=True)
    
    conducted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    application = relationship("Application", back_populates="evc_visits")
    institution = relationship("Institution", back_populates="evc_visits")
    coordinator = relationship("User")

    @property
    def application_number(self):
        return self.application.application_number if self.application else None

    @property
    def institution_name(self):
        return self.institution.name if self.institution else None

