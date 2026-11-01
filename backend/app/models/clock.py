import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class ClockInterval(Base):
    __tablename__ = "clock_intervals"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    clock_type = Column(String(50), nullable=False, index=True)  # "INSTITUTION" or "OFFICIAL"
    stage_key = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)  # Null means active interval
    elapsed_seconds = Column(Float, default=0.0)
    is_paused = Column(Boolean, default=False)
    pause_reason = Column(String(255), nullable=True)
    rule_version = Column(String(50), default="AICTE-APH-2026-v1.0")
    calculation_details = Column(JSON, default=dict)  # Explanation of calculation
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="clock_intervals")

class ClockPauseLog(Base):
    __tablename__ = "clock_pause_logs"

    id = Column(Integer, primary_key=True, index=True)
    interval_id = Column(Integer, ForeignKey("clock_intervals.id", ondelete="CASCADE"), nullable=False, index=True)
    paused_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    pause_start = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    pause_end = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=False)
    authorized_clause = Column(String(100), nullable=True)  # E.g. "APH 2026 Cl. 4.2 - Public Hearing Stay"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
