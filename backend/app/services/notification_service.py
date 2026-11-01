import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationDeliveryAttempt, NotificationType
from app.models.application import Application
from app.models.compliance import Undertaking, UndertakingStatus
from app.models.document import Document
from app.models.user import User, RoleEnum

class NotificationService:
    @classmethod
    def run_deadline_and_escalation_engine(cls, db: Session) -> Dict[str, Any]:
        now = datetime.datetime.utcnow()
        notifications_created = 0
        escalations_triggered = 0

        # 1. Overdue Applications
        overdue_apps = db.query(Application).filter(
            Application.status == "IN_PROGRESS",
            Application.current_deadline.isnot(None),
            Application.current_deadline < now
        ).all()

        for app in overdue_apps:
            # Check if overdue notification already sent in last 24h
            existing = db.query(Notification).filter(
                Notification.related_application_id == app.id,
                Notification.notification_type == NotificationType.OVERDUE,
                Notification.created_at >= now - datetime.timedelta(hours=24)
            ).first()

            if not existing:
                # Notify assigned official
                officials = []
                if app.assigned_official_id:
                    off = db.query(User).filter(User.id == app.assigned_official_id).first()
                    if off:
                        officials.append(off)
                if not officials:
                    officials = db.query(User).filter(User.role == RoleEnum.SCRUTINY_OFFICER).limit(2).all()

                for off in officials:
                    notif = Notification(
                        user_id=off.id,
                        title=f"OVERDUE: Application #{app.application_number}",
                        message=f"Application #{app.application_number} in stage {app.current_stage_key} exceeded its deadline on {app.current_deadline.strftime('%Y-%m-%d %H:%M')}.",
                        notification_type=NotificationType.OVERDUE,
                        severity="CRITICAL",
                        related_application_id=app.id,
                        related_entity_type="APPLICATION",
                        related_entity_id=app.id,
                        action_link=f"/official/applications/{app.id}",
                        due_at=app.current_deadline
                    )
                    db.add(notif)
                    notifications_created += 1

                # If overdue by more than 48 hours, escalate to Bureau Authority & Regional Officer
                hours_overdue = (now - app.current_deadline).total_seconds() / 3600.0
                if hours_overdue > 48.0:
                    escalation_existing = db.query(Notification).filter(
                        Notification.related_application_id == app.id,
                        Notification.notification_type == NotificationType.ESCALATION,
                        Notification.created_at >= now - datetime.timedelta(hours=48)
                    ).first()

                    if not escalation_existing:
                        supervisors = db.query(User).filter(
                            User.role.in_([RoleEnum.BUREAU_AUTHORITY, RoleEnum.REGIONAL_OFFICER, RoleEnum.ADMIN]),
                            User.is_active == True
                        ).all()

                        for sup in supervisors:
                            esc_notif = Notification(
                                user_id=sup.id,
                                title=f"ESCALATION: Stalled Application #{app.application_number}",
                                message=f"Application #{app.application_number} is {round(hours_overdue, 1)} hours overdue in stage {app.current_stage_key}. Immediate administrative intervention required.",
                                notification_type=NotificationType.ESCALATION,
                                severity="CRITICAL",
                                is_escalated=True,
                                related_application_id=app.id,
                                related_entity_type="APPLICATION",
                                related_entity_id=app.id,
                                action_link=f"/official/applications/{app.id}",
                                due_at=app.current_deadline
                            )
                            db.add(esc_notif)
                            escalations_triggered += 1

        # 2. Overdue Compliance Undertakings
        overdue_uts = db.query(Undertaking).filter(
            Undertaking.status.in_([UndertakingStatus.PENDING_SUBMISSION, UndertakingStatus.CORRECTION_REQUESTED]),
            Undertaking.due_date < now
        ).all()

        for ut in overdue_uts:
            ut.status = UndertakingStatus.OVERDUE
            # Notify institution
            inst_users = db.query(User).filter(
                User.institution_id == ut.institution_id,
                User.is_active == True
            ).all()
            for u in inst_users:
                notif = Notification(
                    user_id=u.id,
                    title=f"OVERDUE COMPLIANCE: {ut.title}",
                    message=f"Compliance undertaking {ut.undertaking_code} ({ut.requirement_clause}) is overdue. Please submit evidence immediately.",
                    notification_type=NotificationType.OVERDUE,
                    severity="CRITICAL",
                    related_application_id=ut.application_id,
                    related_entity_type="UNDERTAKING",
                    related_entity_id=ut.id,
                    action_link=f"/institution/compliance/{ut.id}",
                    due_at=ut.due_date
                )
                db.add(notif)
                notifications_created += 1

        # 3. Approaching Document Expiries (< 30 days)
        near_expiry_docs = db.query(Document).filter(
            Document.is_current == True,
            Document.expiry_date.isnot(None),
            Document.expiry_date > now,
            Document.expiry_date <= now + datetime.timedelta(days=30)
        ).all()

        for doc in near_expiry_docs:
            existing = db.query(Notification).filter(
                Notification.related_entity_type == "DOCUMENT",
                Notification.related_entity_id == doc.id,
                Notification.notification_type == NotificationType.DOCUMENT_EXPIRY,
                Notification.created_at >= now - datetime.timedelta(days=7)
            ).first()

            if not existing:
                inst_users = db.query(User).filter(
                    User.institution_id == doc.institution_id,
                    User.is_active == True
                ).all()
                for u in inst_users:
                    notif = Notification(
                        user_id=u.id,
                        title=f"Document Expiring Soon: {doc.title}",
                        message=f"Your {doc.document_type.replace('_', ' ')} expires on {doc.expiry_date.strftime('%Y-%m-%d')}. Submit renewal evidence to avoid compliance holds.",
                        notification_type=NotificationType.DOCUMENT_EXPIRY,
                        severity="WARNING",
                        related_application_id=doc.application_id,
                        related_entity_type="DOCUMENT",
                        related_entity_id=doc.id,
                        action_link=f"/institution/documents",
                        due_at=doc.expiry_date
                    )
                    db.add(notif)
                    notifications_created += 1

        db.commit()
        return {
            "timestamp": now.isoformat(),
            "notifications_created": notifications_created,
            "escalations_triggered": escalations_triggered
        }
