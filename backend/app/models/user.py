import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class RoleEnum:
    INSTITUTION = "INSTITUTION"
    SCRUTINY_OFFICER = "SCRUTINY_OFFICER"
    EVC_COORDINATOR = "EVC_COORDINATOR"
    DOCUMENT_VERIFIER = "DOCUMENT_VERIFIER"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    REGIONAL_OFFICER = "REGIONAL_OFFICER"
    BUREAU_AUTHORITY = "BUREAU_AUTHORITY"
    ADMIN = "ADMIN"

    ALL_ROLES = [
        INSTITUTION, SCRUTINY_OFFICER, EVC_COORDINATOR, DOCUMENT_VERIFIER,
        COMPLIANCE_OFFICER, REGIONAL_OFFICER, BUREAU_AUTHORITY, ADMIN
    ]

    OFFICIAL_ROLES = [
        SCRUTINY_OFFICER, EVC_COORDINATOR, DOCUMENT_VERIFIER,
        COMPLIANCE_OFFICER, REGIONAL_OFFICER, BUREAU_AUTHORITY
    ]

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True, default=RoleEnum.INSTITUTION)
    designation = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)  # Northern, Western, Southern, Eastern, Central, etc.
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    institution = relationship("Institution", back_populates="users")
    assigned_applications = relationship("Application", back_populates="assigned_official", foreign_keys="Application.assigned_official_id")
    audit_events = relationship("AuditEvent", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
