import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    application_number = Column(String(50), unique=True, index=True, nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(20), nullable=False, default="2026-2027")
    application_type = Column(String(100), nullable=False, default="EXTENSION_OF_APPROVAL")
    # EXTENSION_OF_APPROVAL, NEW_INSTITUTE, INCREASE_INTAKE, CLOSURE_OF_COURSE, CHANGE_OF_SITE

    current_stage_key = Column(String(50), nullable=False, default="DRAFT", index=True)
    workflow_code = Column(String(50), default="APPROVAL_PROCESS_2026")
    assigned_official_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Declarations from Institution
    declared_land_acres = Column(String(50), nullable=True)
    declared_builtup_sqm = Column(String(50), nullable=True)
    declared_intake = Column(Integer, nullable=True)
    declared_faculty_count = Column(Integer, nullable=True)
    application_data = Column(JSON, default=dict)  # Complete form submission

    clarification_notes = Column(Text, nullable=True)
    resubmission_count = Column(Integer, default=0)
    current_deadline = Column(DateTime, nullable=True)
    
    status = Column(String(50), default="IN_PROGRESS", index=True) # IN_PROGRESS, APPROVED, REJECTED, WITHDRAWN
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    institution = relationship("Institution", back_populates="applications")
    assigned_official = relationship("User", back_populates="assigned_applications", foreign_keys=[assigned_official_id])
    stage_history = relationship("StageHistory", back_populates="application", cascade="all, delete-orphan", order_by="StageHistory.created_at")
    clock_intervals = relationship("ClockInterval", back_populates="application", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    scrutiny_reports = relationship("ScrutinyReport", back_populates="application", cascade="all, delete-orphan")
    evc_visits = relationship("EVCVisit", back_populates="application", cascade="all, delete-orphan")
    undertakings = relationship("Undertaking", back_populates="application", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="application")

class StageHistory(Base):
    __tablename__ = "stage_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    from_stage = Column(String(50), nullable=False)
    to_stage = Column(String(50), nullable=False)
    transition_name = Column(String(100), nullable=True)
    transitioned_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    application = relationship("Application", back_populates="stage_history")
    transitioned_by = relationship("User")
