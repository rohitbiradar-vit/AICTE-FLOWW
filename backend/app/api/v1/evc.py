import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, require_roles
from app.models.user import User, RoleEnum
from app.models.evc import EVCVisit, EVCStatus
from app.models.application import Application
from app.schemas.evc import EVCVisitCreate, EVCVisitResponse, EVCReportSubmit
from app.services.evc_service import EVCService
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/evc", tags=["EVC Management"])

@router.get("", response_model=List[EVCVisitResponse])
def list_evc_visits(
    application_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(EVCVisit)

    if current_user.role == RoleEnum.INSTITUTION:
        query = query.filter(EVCVisit.institution_id == current_user.institution_id)
    if application_id:
        query = query.filter(EVCVisit.application_id == application_id)
    if status_filter:
        query = query.filter(EVCVisit.status == status_filter)

    return query.order_by(EVCVisit.proposed_date.desc()).all()

@router.post("/schedule", response_model=EVCVisitResponse)
def schedule_evc_visit(
    req: EVCVisitCreate,
    current_user: User = Depends(require_roles([RoleEnum.EVC_COORDINATOR, RoleEnum.REGIONAL_OFFICER, RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    visit = EVCService.schedule_visit(
        db=db,
        application_id=req.application_id,
        proposed_date=req.proposed_date,
        assigned_officers=req.assigned_officers,
        coordinator_user=current_user
    )

    log_audit_event(
        db=db,
        action="EVC_SCHEDULED",
        entity_type="EVC_VISIT",
        entity_id=visit.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={
            "application_id": req.application_id,
            "proposed_date": req.proposed_date.isoformat(),
            "reference": visit.visit_reference
        }
    )
    db.commit()

    return visit

@router.put("/{visit_id}/checklist", response_model=EVCVisitResponse)
def update_evc_checklist(
    visit_id: int,
    checklist: List[dict],
    current_user: User = Depends(require_roles(RoleEnum.OFFICIAL_ROLES + [RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    return EVCService.update_checklist(db, visit_id, checklist)

@router.post("/{visit_id}/report", response_model=EVCVisitResponse)
def submit_evc_report(
    visit_id: int,
    visit_outcome: str = Form(...),
    report_summary: str = Form(...),
    deficiencies_found: Optional[str] = Form(None), # comma-separated or text
    follow_up_required: bool = Form(False),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(require_roles([RoleEnum.EVC_COORDINATOR, RoleEnum.REGIONAL_OFFICER, RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    deficiencies = [d.strip() for d in deficiencies_found.split(",")] if deficiencies_found else []

    visit = EVCService.submit_report(
        db=db,
        visit_id=visit_id,
        visit_outcome=visit_outcome,
        report_summary=report_summary,
        deficiencies_found=deficiencies,
        follow_up_required=follow_up_required,
        file=file
    )

    log_audit_event(
        db=db,
        action="EVC_REPORT_SUBMITTED",
        entity_type="EVC_VISIT",
        entity_id=visit.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"outcome": visit_outcome}
    )
    db.commit()

    return visit

@router.get("/{visit_id}/download-report")
def download_evc_report(
    visit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    visit = db.query(EVCVisit).filter(EVCVisit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="EVC visit not found")

    # Authorisation check:
    # Institutions can only download reports for their own visits
    if current_user.role == RoleEnum.INSTITUTION:
        if visit.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        if visit.status not in [EVCStatus.COMPLETED, EVCStatus.REPORT_SUBMITTED]:
            raise HTTPException(status_code=403, detail="EVC report is not yet available for download")
    elif current_user.role not in RoleEnum.OFFICIAL_ROLES and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if not visit.report_file_path:
        raise HTTPException(status_code=404, detail="No report file available for this EVC visit")

    # Security: Path traversal protection
    storage_dir = os.path.abspath(settings.STORAGE_DIR)
    file_path = os.path.abspath(visit.report_file_path)
    if not file_path.startswith(storage_dir):
        raise HTTPException(status_code=403, detail="Access denied: invalid file path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Underlying report file not found in storage")

    log_audit_event(
        db=db,
        action="EVC_REPORT_DOWNLOAD",
        entity_type="EVC_VISIT",
        entity_id=visit.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={
            "reference": visit.visit_reference,
            "filename": visit.report_filename
        }
    )
    db.commit()

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=visit.report_filename or f"{visit.visit_reference}_report.pdf"
    )

