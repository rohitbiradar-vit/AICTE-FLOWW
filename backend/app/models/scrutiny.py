import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class PriorityBands:
    STANDARD = "STANDARD"   # 0-24
    ENHANCED = "ENHANCED"   # 25-74
    HIGH = "HIGH"           # 75-100

class ScrutinyReport(Base):
    __tablename__ = "scrutiny_reports"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    report_version = Column(Integer, default=1, nullable=False)
    
    # Priority Scoring
    priority_score = Column(Integer, nullable=False)  # 0 to 100
    priority_band = Column(String(50), nullable=False) # STANDARD, ENHANCED, HIGH
    score_formula_breakdown = Column(JSON, nullable=False) # Factors, weights, explanations
    
    # Scrutiny Findings & Inventories
    document_inventory = Column(JSON, default=list) # List of documents & versions inspected
    extracted_summary = Column(JSON, default=dict)  # Merged facts
    missing_evidence = Column(JSON, default=list)   # Mandatory documents missing
    inconsistencies = Column(JSON, default=list)    # Cross-document mismatches with citations
    expiry_findings = Column(JSON, default=list)    # Expired or near-expiry docs
    low_confidence_extractions = Column(JSON, default=list)
    findings_requiring_human_review = Column(JSON, default=list)
    rules_checked = Column(JSON, default=list)      # All statutory rules validated
    suggested_actions = Column(JSON, default=list)  # Recommendation for Scrutiny Officer
    
    # Official Review & Override
    reviewer_decision = Column(String(50), default="PENDING") # PENDING, AGREED, OVERRIDDEN, RETURN_FOR_CLARIFICATION
    reviewer_notes = Column(Text, nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    application = relationship("Application", back_populates="scrutiny_reports")
    reviewed_by = relationship("User")
