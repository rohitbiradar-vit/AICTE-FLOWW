import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class StageKeys:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    INITIAL_SCRUTINY = "INITIAL_SCRUTINY"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    RESUBMITTED = "RESUBMITTED"
    FURTHER_REVIEW = "FURTHER_REVIEW"
    EVC_SCHEDULED = "EVC_SCHEDULED"
    EVC_COMPLETED = "EVC_COMPLETED"
    COMMITTEE_REVIEW = "COMMITTEE_REVIEW"
    FINAL_APPROVAL = "FINAL_APPROVAL"
    REJECTED = "REJECTED"

class ClockAttribution:
    INSTITUTION = "INSTITUTION"
    OFFICIAL = "OFFICIAL"
    PAUSED = "PAUSED"

class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)  # e.g. "APPROVAL_PROCESS_2026"
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    stages = relationship("WorkflowStage", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStage.stage_order")
    transitions = relationship("WorkflowTransition", back_populates="workflow", cascade="all, delete-orphan")
    deadline_rules = relationship("DeadlineRule", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowStage(Base):
    __tablename__ = "workflow_stages"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_key = Column(String(50), nullable=False, index=True)
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    sla_hours = Column(Integer, default=72)  # Service Level Agreement in hours
    clock_attribution = Column(String(50), nullable=False, default=ClockAttribution.OFFICIAL)
    allowed_roles = Column(JSON, default=list)  # Roles who can act in this stage
    is_terminal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("WorkflowDefinition", back_populates="stages")

class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    from_stage_key = Column(String(50), nullable=False, index=True)
    to_stage_key = Column(String(50), nullable=False, index=True)
    transition_name = Column(String(100), nullable=False)
    allowed_roles = Column(JSON, default=list)  # Which roles can trigger this transition
    requires_reason = Column(Boolean, default=False)
    prerequisites = Column(JSON, default=dict)  # e.g. {"require_documents": [...], "require_evc": bool}
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("WorkflowDefinition", back_populates="transitions")

class DeadlineRule(Base):
    __tablename__ = "deadline_rules"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False)
    stage_key = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    max_duration_hours = Column(Integer, nullable=False)
    warning_threshold_hours = Column(Integer, default=24)  # Trigger warning when remaining hours < threshold
    escalation_role = Column(String(50), nullable=True)     # Who to escalate to if overdue
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    workflow = relationship("WorkflowDefinition", back_populates="deadline_rules")

class HolidayRule(Base):
    __tablename__ = "holiday_rules"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    name = Column(String(150), nullable=False)
    is_recurring = Column(Boolean, default=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
