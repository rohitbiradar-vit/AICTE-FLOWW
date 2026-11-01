import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True) # STAGE_TRANSITION, DOCUMENT_UPLOAD, DOCUMENT_VERIFIED, SCRUTINY_OVERRIDE, CLOCK_PAUSE, EVC_SCHEDULED, UNDERTAKING_VERIFIED
    entity_type = Column(String(50), nullable=False, index=True) # APPLICATION, DOCUMENT, EVC, UNDERTAKING, WORKFLOW
    entity_id = Column(Integer, nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_events")
