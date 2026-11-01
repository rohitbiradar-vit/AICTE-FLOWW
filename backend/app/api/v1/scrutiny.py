from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User, RoleEnum
from app.models.application import Application
from app.models.scrutiny import ScrutinyReport
from app.schemas.scrutiny import ScrutinyReportResponse, ScrutinyReviewRequest
from app.services.ai_scrutiny_engine import AIScrutinyEngine
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/scrutiny", tags=["AI Scrutiny"])

@router.post("/applications/{application_id}/generate", response_model=ScrutinyReportResponse)
def trigger_scrutiny_pipeline(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role == RoleEnum.INSTITUTION and app.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    report = AIScrutinyEngine.generate_scrutiny_report(db, application_id)

    log_audit_event(
        db=db,
        action="GENERATE_SCRUTINY_REPORT",
        entity_type="SCRUTINY_REPORT",
        entity_id=report.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={
            "application_id": application_id,
            "priority_score": report.priority_score,
            "priority_band": report.priority_band
        }
    )
    db.commit()

    return report

@router.get("/applications/{application_id}/latest", response_model=ScrutinyReportResponse)
def get_latest_scrutiny_report(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role == RoleEnum.INSTITUTION and app.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    report = db.query(ScrutinyReport).filter(
        ScrutinyReport.application_id == application_id
    ).order_by(ScrutinyReport.report_version.desc()).first()

    if not report:
        # Auto-generate if not yet generated
        report = AIScrutinyEngine.generate_scrutiny_report(db, application_id)

    return report

@router.post("/reports/{report_id}/review", response_model=ScrutinyReportResponse)
def record_scrutiny_review(
    report_id: int,
    req: ScrutinyReviewRequest,
    current_user: User = Depends(require_roles(RoleEnum.OFFICIAL_ROLES + [RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    report = AIScrutinyEngine.record_official_review(
        db=db,
        report_id=report_id,
        user=current_user,
        decision=req.decision,
        notes=req.notes
    )

    log_audit_event(
        db=db,
        action="SCRUTINY_REVIEW_DECISION",
        entity_type="SCRUTINY_REPORT",
        entity_id=report_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"decision": req.decision, "notes": req.notes}
    )
    db.commit()

    return report
