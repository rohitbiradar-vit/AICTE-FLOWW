import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class DocumentTypes:
    LAND_DEED = "LAND_DEED"
    BUILDING_PLAN = "BUILDING_PLAN"
    AICTE_APPROVAL_PREV = "AICTE_APPROVAL_PREV"
    AUDITED_FINANCIALS = "AUDITED_FINANCIALS"
    FACULTY_LIST = "FACULTY_LIST"
    FIRE_SAFETY_CERT = "FIRE_SAFETY_CERT"
    NOC_AFFILIATING_UNIVERSITY = "NOC_AFFILIATING_UNIVERSITY"
    OCCUPANCY_CERTIFICATE = "OCCUPANCY_CERTIFICATE"

    MANDATORY_DOCUMENTS = [
        LAND_DEED,
        BUILDING_PLAN,
        FIRE_SAFETY_CERT,
        NOC_AFFILIATING_UNIVERSITY,
        FACULTY_LIST
    ]

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_uuid = Column(String(100), unique=True, index=True, nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    
    document_type = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_filename = Column(String(255), nullable=False)  # Server controlled path
    file_path = Column(Text, nullable=False)                 # Private path
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    
    version = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)
    
    # Expiry and Validity
    issue_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True, index=True)
    requires_renewal = Column(Boolean, default=False)
    
    # Official Verification
    verification_status = Column(String(50), default="PENDING", index=True) # PENDING, VERIFIED, REJECTED, REQUIRES_CLARIFICATION
    verification_notes = Column(Text, nullable=True)
    verified_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    institution = relationship("Institution", back_populates="documents")
    application = relationship("Application", back_populates="documents")
    extractions = relationship("DocumentExtraction", back_populates="document", cascade="all, delete-orphan")
    findings = relationship("DocumentValidationFinding", back_populates="document", cascade="all, delete-orphan")
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])

class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    extraction_method = Column(String(50), default="OCR_AND_TEXT") # DIGITAL_TEXT, TESSERACT_OCR, HYBRID_RULES
    extracted_text_preview = Column(Text, nullable=True)            # Snippet only (no sensitive leaks)
    extracted_fields = Column(JSON, default=dict)                   # E.g. {"institution_name": ..., "land_area": ..., "expiry_date": ...}
    confidence_scores = Column(JSON, default=dict)                  # E.g. {"institution_name": 0.95, "land_area": 0.88}
    overall_confidence = Column(Float, default=1.0)
    processing_status = Column(String(50), default="COMPLETED")     # COMPLETED, FAILED, RETRY_PENDING
    page_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="extractions")

class DocumentValidationFinding(Base):
    __tablename__ = "document_validation_findings"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_type = Column(String(50), nullable=False) # MISSING_EVIDENCE, INCONSISTENCY, EXPIRED, LOW_CONFIDENCE, REQUIRES_MANUAL_REVIEW
    severity = Column(String(50), default="HIGH")     # LOW, MEDIUM, HIGH, CRITICAL
    field_name = Column(String(100), nullable=True)
    declared_value = Column(String(255), nullable=True)
    extracted_value = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    citation_page = Column(Integer, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="findings")
