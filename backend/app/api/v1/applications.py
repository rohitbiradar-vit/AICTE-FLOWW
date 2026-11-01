import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User, RoleEnum
from app.models.application import Application, StageHistory
from app.models.institution import Institution
from app.models.workflow import StageKeys, ClockAttribution
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse,
    TransitionRequest, ClockPauseRequest
)
from app.services.workflow_engine import WorkflowEngine
from app.services.dual_clock_engine import DualClockEngine
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/applications", tags=["Applications"])

def _format_app_response(app: Application) -> dict:
    return {
        "id": app.id,
        "application_number": app.application_number,
        "institution_id": app.institution_id,
        "institution_name": app.institution.name if app.institution else None,
        "academic_year": app.academic_year,
        "application_type": app.application_type,
        "current_stage_key": app.current_stage_key,
        "workflow_code": app.workflow_code,
        "assigned_official_id": app.assigned_official_id,
        "assigned_official_name": app.assigned_official.full_name if app.assigned_official else None,
        "declared_land_acres": app.declared_land_acres,
        "declared_builtup_sqm": app.declared_builtup_sqm,
        "declared_intake": app.declared_intake,
        "declared_faculty_count": app.declared_faculty_count,
        "application_data": app.application_data,
        "clarification_notes": app.clarification_notes,
        "resubmission_count": app.resubmission_count,
        "current_deadline": app.current_deadline,
        "status": app.status,
        "submitted_at": app.submitted_at,
        "created_at": app.created_at,
        "updated_at": app.updated_at
    }

@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    stage: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Application)

    # Server-enforced institution data isolation!
    if current_user.role == RoleEnum.INSTITUTION:
        if not current_user.institution_id:
            return []
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif current_user.role in [RoleEnum.REGIONAL_OFFICER] and current_user.region:
        query = query.join(Institution).filter(Institution.region == current_user.region)

    if stage:
        query = query.filter(Application.current_stage_key == stage)
    if status_filter:
        query = query.filter(Application.status == status_filter)
    if search:
        query = query.join(Institution).filter(
            (Application.application_number.ilike(f"%{search}%")) |
            (Institution.name.ilike(f"%{search}%"))
        )

    apps = query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
    return [_format_app_response(a) for a in apps]

@router.post("", response_model=ApplicationResponse)
def create_application(
    request_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != RoleEnum.INSTITUTION or not current_user.institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered institutional users can initiate new approval applications."
        )

    app_num = f"AICTE-{datetime.date.today().year}-{uuid.uuid4().hex[:6].upper()}"
    app = Application(
        application_number=app_num,
        institution_id=current_user.institution_id,
        academic_year=request_data.academic_year,
        application_type=request_data.application_type,
        current_stage_key=StageKeys.DRAFT,
        declared_land_acres=request_data.declared_land_acres,
        declared_builtup_sqm=request_data.declared_builtup_sqm,
        declared_intake=request_data.declared_intake,
        declared_faculty_count=request_data.declared_faculty_count,
        application_data=request_data.application_data or {},
        status="IN_PROGRESS"
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    # Start draft institutional clock
    DualClockEngine.start_interval(db, app.id, StageKeys.DRAFT, ClockAttribution.INSTITUTION)
    db.commit()

    log_audit_event(
        db=db,
        action="CREATE_APPLICATION",
        entity_type="APPLICATION",
        entity_id=app.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"application_number": app_num}
    )
    db.commit()

    return _format_app_response(app)

@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Isolation check
    if current_user.role == RoleEnum.INSTITUTION and app.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized: You cannot access records belonging to another institution.")

    return _format_app_response(app)

@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    update_data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role == RoleEnum.INSTITUTION:
        if app.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        if app.current_stage_key not in [StageKeys.DRAFT, StageKeys.CLARIFICATION_REQUIRED]:
            raise HTTPException(status_code=400, detail=f"Application in stage '{app.current_stage_key}' cannot be edited.")

    for field, val in update_data.model_dump(exclude_unset=True).items():
        setattr(app, field, val)

    app.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(app)
    return _format_app_response(app)

@router.post("/{application_id}/transition", response_model=ApplicationResponse)
def transition_application(
    application_id: int,
    req: TransitionRequest,
    http_req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role == RoleEnum.INSTITUTION and app.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    client_ip = http_req.client.host if http_req.client else None
    updated_app = WorkflowEngine.execute_transition(
        db=db,
        application=app,
        target_stage_key=req.target_stage_key,
        user=current_user,
        reason=req.reason,
        metadata_json=req.metadata_json,
        ip_address=client_ip
    )
    return _format_app_response(updated_app)

@router.get("/{application_id}/history")
def get_application_history(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if current_user.role == RoleEnum.INSTITUTION and app.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    history = db.query(StageHistory).filter(
        StageHistory.application_id == application_id
    ).order_by(StageHistory.created_at.asc()).all()

    return [
        {
            "id": h.id,
            "from_stage": h.from_stage,
            "to_stage": h.to_stage,
            "transition_name": h.transition_name,
            "transitioned_by_user_id": h.transitioned_by_user_id,
            "transitioned_by_name": h.transitioned_by.full_name if h.transitioned_by else "System",
            "reason": h.reason,
            "metadata_json": h.metadata_json,
            "created_at": h.created_at.isoformat()
        }
        for h in history
    ]

# Dual-Clock Endpoints
@router.get("/{application_id}/clock-summary")
def get_clock_summary(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if current_user.role == RoleEnum.INSTITUTION and app.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return DualClockEngine.get_application_clock_summary(db, application_id)

@router.post("/{application_id}/clock/pause")
def pause_application_clock(
    application_id: int,
    req: ClockPauseRequest,
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.BUREAU_AUTHORITY, RoleEnum.REGIONAL_OFFICER])),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    success = DualClockEngine.pause_clock(
        db=db,
        application_id=application_id,
        reason=req.reason,
        authorized_clause=req.authorized_clause,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause clock: No active unpaused clock interval found.")

    log_audit_event(
        db=db,
        action="CLOCK_PAUSE",
        entity_type="APPLICATION",
        entity_id=application_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"reason": req.reason, "clause": req.authorized_clause}
    )
    db.commit()
    return {"message": "Clock paused successfully", "application_id": application_id}

@router.post("/{application_id}/clock/resume")
def resume_application_clock(
    application_id: int,
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.BUREAU_AUTHORITY, RoleEnum.REGIONAL_OFFICER])),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    success = DualClockEngine.resume_clock(db=db, application_id=application_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume clock: Application clock is not currently paused.")

    log_audit_event(
        db=db,
        action="CLOCK_RESUME",
        entity_type="APPLICATION",
        entity_id=application_id,
        user_id=current_user.id,
        user_email=current_user.email
    )
    db.commit()
    return {"message": "Clock resumed successfully", "application_id": application_id}
