import io
import csv
import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User, RoleEnum
from app.models.institution import Institution
from app.models.application import Application
from app.models.workflow import StageKeys, WorkflowDefinition, ClockAttribution
from app.models.clock import ClockInterval
from app.models.document import Document
from app.models.compliance import Undertaking, UndertakingStatus
from app.models.evc import EVCVisit, EVCStatus
from app.models.scrutiny import ScrutinyReport, PriorityBands
from app.models.notification import Notification
from app.models.audit import AuditEvent
from app.core.config import settings

router = APIRouter(prefix="/dashboards", tags=["Dashboards & Analytics"])

@router.get("/institution")
def get_institution_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != RoleEnum.INSTITUTION or not current_user.institution_id:
        raise HTTPException(status_code=403, detail="Institution portal access required.")

    inst_id = current_user.institution_id
    now = datetime.datetime.utcnow()

    # Real DB queries
    apps = db.query(Application).filter(Application.institution_id == inst_id).all()
    total_apps = len(apps)
    in_progress_apps = sum(1 for a in apps if a.status == "IN_PROGRESS")
    approved_apps = sum(1 for a in apps if a.status == "APPROVED")
    rejected_apps = sum(1 for a in apps if a.status == "REJECTED")

    stage_distribution: Dict[str, int] = {}
    for a in apps:
        stage_distribution[a.current_stage_key] = stage_distribution.get(a.current_stage_key, 0) + 1

    pending_clarifications = sum(1 for a in apps if a.current_stage_key == StageKeys.CLARIFICATION_REQUIRED)

    # Compliance undertakings
    uts = db.query(Undertaking).filter(Undertaking.institution_id == inst_id).all()
    pending_compliance = sum(1 for u in uts if u.status in [UndertakingStatus.PENDING_SUBMISSION, UndertakingStatus.CORRECTION_REQUESTED])
    overdue_compliance = sum(1 for u in uts if u.due_date < now and u.status in [UndertakingStatus.PENDING_SUBMISSION, UndertakingStatus.CORRECTION_REQUESTED, UndertakingStatus.OVERDUE])

    # Expiring documents
    expiring_docs_count = db.query(Document).filter(
        Document.institution_id == inst_id,
        Document.is_current == True,
        Document.expiry_date.isnot(None),
        Document.expiry_date <= now + datetime.timedelta(days=60)
    ).count()

    # Unread notifications
    unread_notifs = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return {
        "institution_id": inst_id,
        "metrics": {
            "total_applications": total_apps,
            "in_progress": in_progress_apps,
            "approved": approved_apps,
            "rejected": rejected_apps,
            "pending_clarifications": pending_clarifications,
            "pending_compliance": pending_compliance,
            "overdue_compliance": overdue_compliance,
            "expiring_documents": expiring_docs_count,
            "unread_notifications": unread_notifs
        },
        "stage_distribution": stage_distribution,
        "recent_applications": [
            {
                "id": a.id,
                "application_number": a.application_number,
                "application_type": a.application_type,
                "current_stage": a.current_stage_key,
                "status": a.status,
                "current_deadline": a.current_deadline.isoformat() if a.current_deadline else None,
                "created_at": a.created_at.isoformat()
            }
            for a in apps[:5]
        ]
    }

@router.get("/official")
def get_official_dashboard(
    current_user: User = Depends(require_roles(RoleEnum.OFFICIAL_ROLES + [RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    now = datetime.datetime.utcnow()

    # Query applications
    query = db.query(Application)
    if current_user.role == RoleEnum.REGIONAL_OFFICER and current_user.region:
        query = query.join(Institution).filter(Institution.region == current_user.region)

    apps = query.all()
    total_active = sum(1 for a in apps if a.status == "IN_PROGRESS")
    overdue_count = sum(1 for a in apps if a.status == "IN_PROGRESS" and a.current_deadline and a.current_deadline < now)

    # Stage breakdown
    stage_breakdown: Dict[str, int] = {}
    for a in apps:
        stage_breakdown[a.current_stage_key] = stage_breakdown.get(a.current_stage_key, 0) + 1

    # High-priority scrutiny cases
    high_priority_scrutiny = db.query(ScrutinyReport).join(Application).filter(
        Application.status == "IN_PROGRESS",
        ScrutinyReport.priority_band == PriorityBands.HIGH
    ).order_by(ScrutinyReport.priority_score.desc()).limit(10).all()

    high_priority_cases = [
        {
            "report_id": r.id,
            "application_id": r.application_id,
            "application_number": r.application.application_number if r.application else "",
            "institution_name": r.application.institution.name if (r.application and r.application.institution) else "Unknown",
            "priority_score": r.priority_score,
            "missing_docs_count": len(r.missing_evidence or []),
            "inconsistencies_count": len(r.inconsistencies or []),
            "expired_docs_count": len(r.expiry_findings or []),
            "suggested_action": r.suggested_actions[0] if r.suggested_actions else "Standard review"
        }
        for r in high_priority_scrutiny
    ]

    # EVC Visits
    pending_evc = db.query(EVCVisit).filter(
        EVCVisit.status.in_([EVCStatus.REQUESTED, EVCStatus.SCHEDULED, EVCStatus.IN_PROGRESS])
    ).count()

    # Compliance queue
    compliance_queue_count = db.query(Undertaking).filter(
        Undertaking.status == UndertakingStatus.SUBMITTED
    ).count()

    # Dual-Clock Aggregate averages (hours)
    avg_inst_sec = db.query(func.avg(ClockInterval.elapsed_seconds)).filter(
        ClockInterval.clock_type == ClockAttribution.INSTITUTION
    ).scalar() or 0.0

    avg_off_sec = db.query(func.avg(ClockInterval.elapsed_seconds)).filter(
        ClockInterval.clock_type == ClockAttribution.OFFICIAL
    ).scalar() or 0.0

    # Bottleneck detection: average elapsed hours per stage
    stage_bottlenecks = db.query(
        ClockInterval.stage_key,
        func.avg(ClockInterval.elapsed_seconds).label("avg_sec"),
        func.count(ClockInterval.id).label("count")
    ).group_by(ClockInterval.stage_key).all()

    bottlenecks = [
        {
            "stage_key": b[0],
            "average_hours": round((b[1] or 0.0) / 3600.0, 1),
            "interval_count": b[2]
        }
        for b in stage_bottlenecks
    ]
    bottlenecks.sort(key=lambda x: x["average_hours"], reverse=True)

    return {
        "work_queue_count": total_active,
        "overdue_count": overdue_count,
        "pending_evc_visits": pending_evc,
        "compliance_queue_count": compliance_queue_count,
        "clock_averages": {
            "institution_clock_avg_hours": round(avg_inst_sec / 3600.0, 1),
            "official_clock_avg_hours": round(avg_off_sec / 3600.0, 1)
        },
        "stage_breakdown": stage_breakdown,
        "high_priority_cases": high_priority_cases,
        "bottlenecks": bottlenecks
    }

@router.get("/admin")
def get_admin_dashboard(
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.BUREAU_AUTHORITY])),
    db: Session = Depends(get_db)
):
    total_institutions = db.query(Institution).count()
    total_applications = db.query(Application).count()
    active_applications = db.query(Application).filter(Application.status == "IN_PROGRESS").count()
    approved_applications = db.query(Application).filter(Application.status == "APPROVED").count()
    rejected_applications = db.query(Application).filter(Application.status == "REJECTED").count()

    total_audit_events = db.query(AuditEvent).count()
    recent_audit_events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(15).all()

    # Region-wise breakdown
    regional_counts = db.query(
        Institution.region,
        func.count(Application.id)
    ).join(Application, Application.institution_id == Institution.id).group_by(Institution.region).all()

    regional_distribution = [{"region": r[0], "application_count": r[1]} for r in regional_counts]

    # Escalations count
    escalations_count = db.query(Notification).filter(Notification.is_escalated == True).count()

    return {
        "system_metrics": {
            "total_institutions": total_institutions,
            "total_applications": total_applications,
            "active_applications": active_applications,
            "approved_applications": approved_applications,
            "rejected_applications": rejected_applications,
            "escalations_count": escalations_count,
            "total_audit_events": total_audit_events,
            "active_rule_version": settings.RULE_VERSION
        },
        "regional_distribution": regional_distribution,
        "recent_audit_events": [
            {
                "id": a.id,
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "user_email": a.user_email or "System",
                "details": a.details,
                "created_at": a.created_at.isoformat()
            }
            for a in recent_audit_events
        ]
    }

@router.get("/export/applications-csv")
def export_applications_csv(
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.BUREAU_AUTHORITY, RoleEnum.REGIONAL_OFFICER])),
    db: Session = Depends(get_db)
):
    apps = db.query(Application).join(Institution).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Application Number", "Institution Name", "Region", "Academic Year",
        "Application Type", "Current Stage", "Status", "Submitted At", "Deadline"
    ])

    for a in apps:
        writer.writerow([
            a.application_number,
            a.institution.name if a.institution else "",
            a.institution.region if a.institution else "",
            a.academic_year,
            a.application_type,
            a.current_stage_key,
            a.status,
            a.submitted_at.strftime("%Y-%m-%d %H:%M") if a.submitted_at else "N/A",
            a.current_deadline.strftime("%Y-%m-%d %H:%M") if a.current_deadline else "N/A"
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aicte_applications_export.csv"}
    )
