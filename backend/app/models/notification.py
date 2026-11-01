import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class NotificationType:
    DEADLINE = "DEADLINE"
    OVERDUE = "OVERDUE"
    CLARIFICATION = "CLARIFICATION"
    EVC_VISIT = "EVC_VISIT"
    COMPLIANCE = "COMPLIANCE"
    DOCUMENT_EXPIRY = "DOCUMENT_EXPIRY"
    ESCALATION = "ESCALATION"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default=NotificationType.DEADLINE, nullable=False, index=True)
    severity = Column(String(50), default="INFO") # INFO, WARNING, CRITICAL
    
    related_application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    related_entity_type = Column(String(50), nullable=True) # APPLICATION, UNDERTAKING, EVC, DOCUMENT
    related_entity_id = Column(Integer, nullable=True)
    action_link = Column(String(255), nullable=True)
    
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    is_escalated = Column(Boolean, default=False, nullable=False)
    due_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="notifications")
    application = relationship("Application", back_populates="notifications")
    delivery_attempts = relationship("NotificationDeliveryAttempt", back_populates="notification", cascade="all, delete-orphan")

class NotificationDeliveryAttempt(Base):
    __tablename__ = "notification_delivery_attempts"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), default="IN_APP") # IN_APP, EMAIL_SIMULATED
    attempt_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="DELIVERED") # DELIVERED, FAILED, RETRYING
    error_message = Column(Text, nullable=True)

    notification = relationship("Notification", back_populates="delivery_attempts")
