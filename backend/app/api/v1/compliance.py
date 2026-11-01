import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, require_roles
from app.models.user import User, RoleEnum
from app.models.compliance import Undertaking, UndertakingStatus
from app.schemas.compliance import UndertakingCreate, UndertakingResponse, UndertakingVerifyRequest
from app.services.compliance_service import ComplianceService
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/compliance", tags=["Compliance & Undertakings"])

@router.get("/undertakings", response_model=List[UndertakingResponse])
def list_undertakings(
    application_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Undertaking)

    if current_user.role == RoleEnum.INSTITUTION:
        query = query.filter(Undertaking.institution_id == current_user.institution_id)
    if application_id:
        query = query.filter(Undertaking.application_id == application_id)
    if status_filter:
        query = query.filter(Undertaking.status == status_filter)

    return query.order_by(Undertaking.due_date.asc()).all()

@router.post("/undertakings", response_model=UndertakingResponse)
def create_undertaking(
    req: UndertakingCreate,
    current_user: User = Depends(require_roles([RoleEnum.COMPLIANCE_OFFICER, RoleEnum.SCRUTINY_OFFICER, RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    ut = ComplianceService.create_undertaking(
        db=db,
        institution_id=req.institution_id,
        title=req.title,
        requirement_clause=req.requirement_clause,
        description=req.description,
        due_date=req.due_date,
        application_id=req.application_id,
        created_by_user_id=current_user.id,
        requires_annual_renewal=req.requires_annual_renewal
    )

    log_audit_event(
        db=db,
        action="CREATE_UNDERTAKING",
        entity_type="UNDERTAKING",
        entity_id=ut.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"code": ut.undertaking_code, "due_date": req.due_date.isoformat()}
    )
    db.commit()

    return ut

@router.post("/undertakings/{undertaking_id}/submit-evidence", response_model=UndertakingResponse)
def submit_undertaking_evidence(
    undertaking_id: int,
    evidence_description: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ut = db.query(Undertaking).filter(Undertaking.id == undertaking_id).first()
    if not ut:
        raise HTTPException(status_code=404, detail="Undertaking not found")

    if current_user.role == RoleEnum.INSTITUTION and ut.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    res = ComplianceService.submit_compliance_evidence(
        db=db,
        undertaking_id=undertaking_id,
        evidence_description=evidence_description,
        file=file,
        user=current_user
    )

    log_audit_event(
        db=db,
        action="SUBMIT_COMPLIANCE_EVIDENCE",
        entity_type="UNDERTAKING",
        entity_id=ut.id,
        user_id=current_user.id,
        user_email=current_user.email
    )
    db.commit()

    return res

@router.get("/undertakings/{undertaking_id}/download-evidence")
def download_compliance_evidence(
    undertaking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ut = db.query(Undertaking).filter(Undertaking.id == undertaking_id).first()
    if not ut:
        raise HTTPException(status_code=404, detail="Undertaking not found")

    # Authorisation check:
    # Institutions can only download evidence for their own undertakings
    if current_user.role == RoleEnum.INSTITUTION:
        if ut.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
    elif current_user.role not in RoleEnum.OFFICIAL_ROLES and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if not ut.evidence_file_path:
        raise HTTPException(status_code=404, detail="No compliance evidence uploaded for this undertaking")

    # Security: Path traversal protection
    storage_dir = os.path.abspath(settings.STORAGE_DIR)
    file_path = os.path.abspath(ut.evidence_file_path)
    if not file_path.startswith(storage_dir):
        raise HTTPException(status_code=403, detail="Access denied: invalid file path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Underlying evidence file not found in storage")

    log_audit_event(
        db=db,
        action="COMPLIANCE_EVIDENCE_DOWNLOAD",
        entity_type="UNDERTAKING",
        entity_id=ut.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={
            "undertaking_code": ut.undertaking_code,
            "filename": ut.evidence_filename
        }
    )
    db.commit()

    # Determine media type
    filename = ut.evidence_filename or f"evidence_{ut.undertaking_code}.pdf"
    media_type = "application/pdf"
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        media_type = f"image/{filename.rsplit('.', 1)[-1].lower().replace('jpg', 'jpeg')}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


@router.post("/undertakings/{undertaking_id}/verify", response_model=UndertakingResponse)
def verify_undertaking(
    undertaking_id: int,
    req: UndertakingVerifyRequest,
    current_user: User = Depends(require_roles([RoleEnum.COMPLIANCE_OFFICER, RoleEnum.ADMIN, RoleEnum.REGIONAL_OFFICER])),
    db: Session = Depends(get_db)
):
    res = ComplianceService.verify_undertaking(
        db=db,
        undertaking_id=undertaking_id,
        decision=req.decision,
        verifier=current_user,
        notes=req.notes,
        correction_reason=req.correction_reason
    )

    log_audit_event(
        db=db,
        action="VERIFY_UNDERTAKING",
        entity_type="UNDERTAKING",
        entity_id=undertaking_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"decision": req.decision}
    )
    db.commit()

    return res

@router.get("/document-expiry-register")
def get_document_expiry_register(
    institution_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_inst = institution_id
    if current_user.role == RoleEnum.INSTITUTION:
        target_inst = current_user.institution_id

    return ComplianceService.get_document_expiry_register(db, institution_id=target_inst)
