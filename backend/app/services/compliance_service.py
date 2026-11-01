import datetime
import uuid
import os
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from app.models.compliance import Undertaking, UndertakingStatus
from app.models.document import Document
from app.models.application import Application
from app.models.user import User
from app.core.config import settings

class ComplianceService:
    @classmethod
    def create_undertaking(
        cls,
        db: Session,
        institution_id: int,
        title: str,
        requirement_clause: str,
        description: str,
        due_date: datetime.datetime,
        application_id: Optional[int] = None,
        created_by_user_id: Optional[int] = None,
        requires_annual_renewal: bool = False
    ) -> Undertaking:
        code = f"UT-{datetime.date.today().year}-{uuid.uuid4().hex[:6].upper()}"
        undertaking = Undertaking(
            undertaking_code=code,
            institution_id=institution_id,
            application_id=application_id,
            title=title,
            requirement_clause=requirement_clause,
            description=description,
            due_date=due_date,
            status=UndertakingStatus.PENDING_SUBMISSION,
            requires_annual_renewal=requires_annual_renewal,
            created_by_user_id=created_by_user_id
        )
        db.add(undertaking)
        db.commit()
        db.refresh(undertaking)
        return undertaking

    @classmethod
    def submit_compliance_evidence(
        cls,
        db: Session,
        undertaking_id: int,
        evidence_description: str,
        file: UploadFile,
        user: User
    ) -> Undertaking:
        ut = db.query(Undertaking).filter(Undertaking.id == undertaking_id).first()
        if not ut:
            raise HTTPException(status_code=404, detail="Undertaking not found")

        # Ingestion
        filename = f"evidence_{ut.undertaking_code}_{uuid.uuid4().hex[:6]}.pdf"
        path = os.path.join(settings.STORAGE_DIR, filename)
        contents = file.file.read()
        with open(path, "wb") as f:
            f.write(contents)

        ut.evidence_filename = file.filename or filename
        ut.evidence_file_path = path
        ut.evidence_description = evidence_description
        ut.submission_version = (ut.submission_version or 0) + 1
        ut.submitted_at = datetime.datetime.utcnow()
        ut.status = UndertakingStatus.SUBMITTED
        ut.updated_at = datetime.datetime.utcnow()

        db.commit()
        db.refresh(ut)
        return ut

    @classmethod
    def verify_undertaking(
        cls,
        db: Session,
        undertaking_id: int,
        decision: str, # ACCEPTED, CORRECTION_REQUESTED, REJECTED
        verifier: User,
        notes: Optional[str] = None,
        correction_reason: Optional[str] = None
    ) -> Undertaking:
        ut = db.query(Undertaking).filter(Undertaking.id == undertaking_id).first()
        if not ut:
            raise HTTPException(status_code=404, detail="Undertaking not found")

        if decision == "ACCEPTED":
            ut.status = UndertakingStatus.ACCEPTED
            if ut.requires_annual_renewal:
                ut.renewal_due_date = datetime.datetime.utcnow() + datetime.timedelta(days=365)
        elif decision == "CORRECTION_REQUESTED":
            if not correction_reason:
                raise HTTPException(status_code=400, detail="Correction reason is required when requesting evidence correction.")
            ut.status = UndertakingStatus.CORRECTION_REQUESTED
            ut.correction_reason = correction_reason
        elif decision == "REJECTED":
            ut.status = UndertakingStatus.REJECTED
        else:
            raise HTTPException(status_code=400, detail=f"Invalid verification decision '{decision}'")

        ut.verified_by_user_id = verifier.id
        ut.verification_notes = notes
        ut.verified_at = datetime.datetime.utcnow()
        ut.updated_at = datetime.datetime.utcnow()

        db.commit()
        db.refresh(ut)
        return ut

    @classmethod
    def get_document_expiry_register(
        cls,
        db: Session,
        institution_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = db.query(Document).filter(
            Document.is_current == True,
            Document.expiry_date.isnot(None)
        )
        if institution_id:
            query = query.filter(Document.institution_id == institution_id)

        docs = query.order_by(Document.expiry_date.asc()).all()
        now = datetime.datetime.utcnow()
        register = []

        for d in docs:
            days_remaining = (d.expiry_date - now).days
            if days_remaining < 0:
                expiry_status = "EXPIRED"
            elif days_remaining <= 30:
                expiry_status = "CRITICAL_RENEWAL_REQUIRED"
            elif days_remaining <= 90:
                expiry_status = "UPCOMING_EXPIRY"
            else:
                expiry_status = "VALID"

            register.append({
                "document_id": d.id,
                "document_uuid": d.document_uuid,
                "title": d.title,
                "document_type": d.document_type,
                "institution_id": d.institution_id,
                "institution_name": d.institution.name if d.institution else "Unknown",
                "issue_date": d.issue_date.isoformat() if d.issue_date else None,
                "expiry_date": d.expiry_date.isoformat() if d.expiry_date else None,
                "days_remaining": days_remaining,
                "expiry_status": expiry_status,
                "verification_status": d.verification_status,
                "requires_renewal": d.requires_renewal
            })

        return register
