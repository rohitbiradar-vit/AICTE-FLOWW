from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User, RoleEnum
from app.models.notification import Notification
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
def list_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifs = query.order_by(Notification.created_at.desc()).limit(100).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "notification_type": n.notification_type,
            "severity": n.severity,
            "related_application_id": n.related_application_id,
            "action_link": n.action_link,
            "is_read": n.is_read,
            "is_escalated": n.is_escalated,
            "due_at": n.due_at.isoformat() if n.due_at else None,
            "created_at": n.created_at.isoformat()
        }
        for n in notifs
    ]

@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}

@router.post("/read-all")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}

@router.post("/run-jobs")
def run_deadline_and_escalation_engine(
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.BUREAU_AUTHORITY, RoleEnum.REGIONAL_OFFICER])),
    db: Session = Depends(get_db)
):
    """Manual trigger endpoint to test scheduled deadline tracking and overdue escalations."""
    res = NotificationService.run_deadline_and_escalation_engine(db)
    return res
