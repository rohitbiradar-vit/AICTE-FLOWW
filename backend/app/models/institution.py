import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    aicte_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    institute_type = Column(String(100), default="ENGINEERING_AND_TECHNOLOGY")  # Technical, Management, Pharmacy, Architecture, etc.
    region = Column(String(100), nullable=False)  # Northern, Western, Southern, etc.
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=True)
    address = Column(Text, nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, SUSPENDED, DE-AFFILIATED
    metadata_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="institution")
    applications = relationship("Application", back_populates="institution")
    documents = relationship("Document", back_populates="institution")
    undertakings = relationship("Undertaking", back_populates="institution")
    evc_visits = relationship("EVCVisit", back_populates="institution")
