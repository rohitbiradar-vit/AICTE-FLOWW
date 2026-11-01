import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, require_roles
from app.models.user import User, RoleEnum
from app.models.document import Document, DocumentExtraction, DocumentValidationFinding
from app.models.application import Application
from app.schemas.document import DocumentResponse, DocumentVerifyRequest
from app.services.ai_scrutiny_engine import AIScrutinyEngine
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    institution_id: Optional[int] = Form(None),
    application_id: Optional[int] = Form(None),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_inst_id = institution_id
    if current_user.role == RoleEnum.INSTITUTION:
        target_inst_id = current_user.institution_id
        if not target_inst_id:
            raise HTTPException(status_code=400, detail="User not linked to an institution.")
        # If application_id provided, verify ownership
        if application_id:
            app = db.query(Application).filter(Application.id == application_id).first()
            if not app or app.institution_id != target_inst_id:
                raise HTTPException(status_code=403, detail="Unauthorized access to application.")

    if not target_inst_id:
        raise HTTPException(status_code=400, detail="institution_id is required.")

    doc = AIScrutinyEngine.ingest_document(
        db=db,
        file=file,
        document_type=document_type,
        institution_id=target_inst_id,
        application_id=application_id,
        user=current_user,
        title=title
    )
    db.commit()
    db.refresh(doc)

    log_audit_event(
        db=db,
        action="DOCUMENT_UPLOAD",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={
            "document_type": doc.document_type,
            "version": doc.version,
            "filename": doc.original_filename,
            "sha256": doc.sha256_hash
        }
    )
    db.commit()

    return doc

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    application_id: Optional[int] = None,
    institution_id: Optional[int] = None,
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Document).filter(Document.is_current == True)

    if current_user.role == RoleEnum.INSTITUTION:
        query = query.filter(Document.institution_id == current_user.institution_id)
    elif institution_id:
        query = query.filter(Document.institution_id == institution_id)

    if application_id:
        query = query.filter(Document.application_id == application_id)
    if document_type:
        query = query.filter(Document.document_type == document_type)

    return query.order_by(Document.created_at.desc()).all()

@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Access check: Institutions can only download their own documents
    if current_user.role == RoleEnum.INSTITUTION and doc.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Path traversal protection
    storage_dir = os.path.abspath(settings.STORAGE_DIR)
    file_path = os.path.abspath(doc.file_path)
    if not file_path.startswith(storage_dir):
        raise HTTPException(status_code=403, detail="Access denied: invalid file path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Underlying document file not found in storage.")

    log_audit_event(
        db=db,
        action="DOCUMENT_DOWNLOAD",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        user_id=current_user.id,
        user_email=current_user.email
    )
    db.commit()

    return FileResponse(
        path=doc.file_path,
        media_type=doc.mime_type,
        filename=doc.original_filename
    )

@router.post("/{document_id}/verify", response_model=DocumentResponse)
def verify_document(
    document_id: int,
    req: DocumentVerifyRequest,
    current_user: User = Depends(require_roles(RoleEnum.OFFICIAL_ROLES + [RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.verification_status = req.verification_status
    doc.verification_notes = req.verification_notes
    doc.verified_by_user_id = current_user.id
    if req.issue_date:
        doc.issue_date = req.issue_date
    if req.expiry_date:
        doc.expiry_date = req.expiry_date
        doc.requires_renewal = True

    db.commit()
    db.refresh(doc)

    log_audit_event(
        db=db,
        action="DOCUMENT_VERIFIED",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={
            "status": req.verification_status,
            "notes": req.verification_notes
        }
    )
    db.commit()

    return doc

@router.get("/{document_id}/extractions")
def get_document_extractions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role == RoleEnum.INSTITUTION and doc.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    extractions = db.query(DocumentExtraction).filter(DocumentExtraction.document_id == document_id).all()
    return extractions
