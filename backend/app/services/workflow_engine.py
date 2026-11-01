import datetime
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.application import Application, StageHistory
from app.models.workflow import (
    WorkflowDefinition, WorkflowStage, WorkflowTransition, 
    DeadlineRule, StageKeys, ClockAttribution
)
from app.models.document import Document, DocumentTypes
from app.models.evc import EVCVisit, EVCStatus
from app.models.user import User, RoleEnum
from app.models.notification import Notification, NotificationType
from app.services.dual_clock_engine import DualClockEngine
from app.services.audit_service import log_audit_event

class WorkflowEngine:
    @classmethod
    def get_stage_info(cls, db: Session, stage_key: str, workflow_code: str = "APPROVAL_PROCESS_2026") -> Optional[WorkflowStage]:
        wf = db.query(WorkflowDefinition).filter(
            WorkflowDefinition.code == workflow_code,
            WorkflowDefinition.is_active == True
        ).first()
        if not wf:
            return None
        return db.query(WorkflowStage).filter(
            WorkflowStage.workflow_id == wf.id,
            WorkflowStage.stage_key == stage_key
        ).first()

    @classmethod
    def validate_transition(
        cls,
        db: Session,
        application: Application,
        target_stage_key: str,
        user: User,
        reason: Optional[str] = None
    ) -> WorkflowTransition:
        # 1. Fetch workflow definition
        wf = db.query(WorkflowDefinition).filter(
            WorkflowDefinition.code == application.workflow_code,
            WorkflowDefinition.is_active == True
        ).first()
        if not wf:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Active workflow definition '{application.workflow_code}' not found."
            )

        # 2. Check if transition exists from current_stage to target_stage
        transition = db.query(WorkflowTransition).filter(
            WorkflowTransition.workflow_id == wf.id,
            WorkflowTransition.from_stage_key == application.current_stage_key,
            WorkflowTransition.to_stage_key == target_stage_key
        ).first()

        if not transition:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transition from '{application.current_stage_key}' to '{target_stage_key}'. No configured rule allows this state change."
            )

        # 3. Check role permissions
        if transition.allowed_roles and len(transition.allowed_roles) > 0:
            if user.role not in transition.allowed_roles and user.role != RoleEnum.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User role '{user.role}' is not authorized to perform transition '{transition.transition_name}'. Allowed: {transition.allowed_roles}"
                )

        # 4. Check if reason is mandatory
        if transition.requires_reason and (not reason or not reason.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A mandatory detailed reason is required for transition '{transition.transition_name}'."
            )

        # 5. Check prerequisites
        prereqs = transition.prerequisites or {}

        # 5a. Mandatory documents check
        if prereqs.get("require_documents"):
            required_doc_types = prereqs["require_documents"]
            existing_doc_types = db.query(Document.document_type).filter(
                Document.application_id == application.id,
                Document.is_current == True
            ).all()
            existing_set = {d[0] for d in existing_doc_types}
            missing = [dt for dt in required_doc_types if dt not in existing_set]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot transition to '{target_stage_key}'. Missing mandatory documents: {missing}"
                )

        # 5b. EVC completion check
        if prereqs.get("require_evc_completed"):
            evc = db.query(EVCVisit).filter(
                EVCVisit.application_id == application.id,
                EVCVisit.status.in_([EVCStatus.COMPLETED, EVCStatus.REPORT_SUBMITTED])
            ).first()
            if not evc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot proceed to Committee Review. Expert Visiting Committee (EVC) report has not been completed."
                )

        return transition

    @classmethod
    def execute_transition(
        cls,
        db: Session,
        application: Application,
        target_stage_key: str,
        user: User,
        reason: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> Application:
        from_stage = application.current_stage_key
        transition = cls.validate_transition(db, application, target_stage_key, user, reason)

        now = datetime.datetime.utcnow()

        # 1. Close current clock interval
        DualClockEngine.close_active_intervals(db, application.id, end_time=now)

        # 2. Determine target stage attribution & SLA
        target_stage_info = cls.get_stage_info(db, target_stage_key, application.workflow_code)
        target_clock_attr = target_stage_info.clock_attribution if target_stage_info else ClockAttribution.OFFICIAL
        sla_hours = target_stage_info.sla_hours if target_stage_info else 72

        # 3. Start new clock interval if not terminal stage
        if not (target_stage_info and target_stage_info.is_terminal):
            DualClockEngine.start_interval(db, application.id, target_stage_key, target_clock_attr, start_time=now)
            application.current_deadline = now + datetime.timedelta(hours=sla_hours)
        else:
            application.current_deadline = None

        # 4. Update Application fields
        application.current_stage_key = target_stage_key
        application.updated_at = now

        if from_stage == StageKeys.DRAFT and target_stage_key == StageKeys.SUBMITTED:
            application.submitted_at = now
            application.status = "IN_PROGRESS"

        if target_stage_key == StageKeys.CLARIFICATION_REQUIRED:
            application.clarification_notes = reason

        if target_stage_key == StageKeys.RESUBMITTED:
            application.resubmission_count = (application.resubmission_count or 0) + 1

        if target_stage_key == StageKeys.FINAL_APPROVAL:
            application.status = "APPROVED"

        if target_stage_key == StageKeys.REJECTED:
            application.status = "REJECTED"

        # 5. Record StageHistory
        history = StageHistory(
            application_id=application.id,
            from_stage=from_stage,
            to_stage=target_stage_key,
            transition_name=transition.transition_name,
            transitioned_by_user_id=user.id,
            reason=reason,
            metadata_json=metadata_json or {},
            created_at=now
        )
        db.add(history)

        # 6. Audit Event
        log_audit_event(
            db=db,
            action="STAGE_TRANSITION",
            entity_type="APPLICATION",
            entity_id=application.id,
            user_id=user.id,
            user_email=user.email,
            ip_address=ip_address,
            details={
                "from_stage": from_stage,
                "to_stage": target_stage_key,
                "transition_name": transition.transition_name,
                "reason": reason
            }
        )

        # 7. Persistent Notifications
        cls._create_transition_notifications(db, application, from_stage, target_stage_key, reason)

        db.commit()
        db.refresh(application)
        return application

    @classmethod
    def _create_transition_notifications(
        cls,
        db: Session,
        application: Application,
        from_stage: str,
        to_stage: str,
        reason: Optional[str]
    ):
        # Notify institution users when application moves to CLARIFICATION_REQUIRED, FINAL_APPROVAL, REJECTED
        if to_stage in [StageKeys.CLARIFICATION_REQUIRED, StageKeys.FINAL_APPROVAL, StageKeys.REJECTED]:
            inst_users = db.query(User).filter(
                User.institution_id == application.institution_id,
                User.is_active == True
            ).all()

            title = f"Application Status Update: {to_stage.replace('_', ' ')}"
            severity = "WARNING" if to_stage in [StageKeys.CLARIFICATION_REQUIRED, StageKeys.REJECTED] else "INFO"
            msg = f"Application #{application.application_number} transitioned to {to_stage}."
            if reason:
                msg += f" Note: {reason}"

            for u in inst_users:
                notif = Notification(
                    user_id=u.id,
                    title=title,
                    message=msg,
                    notification_type=NotificationType.CLARIFICATION if to_stage == StageKeys.CLARIFICATION_REQUIRED else NotificationType.DEADLINE,
                    severity=severity,
                    related_application_id=application.id,
                    related_entity_type="APPLICATION",
                    related_entity_id=application.id,
                    action_link=f"/institution/applications/{application.id}",
                    due_at=application.current_deadline
                )
                db.add(notif)

        # Notify assigned official or scrutiny officers when submitted/resubmitted
        if to_stage in [StageKeys.SUBMITTED, StageKeys.RESUBMITTED]:
            officials = []
            if application.assigned_official_id:
                off = db.query(User).filter(User.id == application.assigned_official_id).first()
                if off:
                    officials.append(off)
            if not officials:
                officials = db.query(User).filter(
                    User.role.in_([RoleEnum.SCRUTINY_OFFICER, RoleEnum.REGIONAL_OFFICER]),
                    User.is_active == True
                ).limit(5).all()

            for off in officials:
                notif = Notification(
                    user_id=off.id,
                    title=f"Application {to_stage}: #{application.application_number}",
                    message=f"Application #{application.application_number} from {application.institution.name if application.institution else 'Institution'} requires scrutiny review.",
                    notification_type=NotificationType.DEADLINE,
                    severity="INFO",
                    related_application_id=application.id,
                    related_entity_type="APPLICATION",
                    related_entity_id=application.id,
                    action_link=f"/official/applications/{application.id}",
                    due_at=application.current_deadline
                )
                db.add(notif)
