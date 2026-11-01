import datetime
import uuid
import os
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from app.models.evc import EVCVisit, EVCStatus
from app.models.application import Application
from app.models.user import User
from app.core.config import settings

class EVCService:
    @classmethod
    def schedule_visit(
        cls,
        db: Session,
        application_id: int,
        proposed_date: datetime.datetime,
        assigned_officers: List[Dict[str, Any]],
        coordinator_user: User
    ) -> EVCVisit:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # Conflict check: Check if any assigned officer is assigned to another active visit on the same date
        date_start = datetime.datetime.combine(proposed_date.date(), datetime.time.min)
        date_end = datetime.datetime.combine(proposed_date.date(), datetime.time.max)

        existing_visits = db.query(EVCVisit).filter(
            EVCVisit.proposed_date >= date_start,
            EVCVisit.proposed_date <= date_end,
            EVCVisit.status.in_([EVCStatus.SCHEDULED, EVCStatus.IN_PROGRESS])
        ).all()

        assigned_emails = {o.get("email") for o in assigned_officers if o.get("email")}
        for v in existing_visits:
            for officer in (v.assigned_officers or []):
                if officer.get("email") in assigned_emails:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Scheduling Conflict: Officer '{officer.get('name')}' ({officer.get('email')}) is already assigned to visit '{v.visit_reference}' on {proposed_date.strftime('%Y-%m-%d')}."
                    )

        reference = f"EVC-{datetime.date.today().year}-{uuid.uuid4().hex[:6].upper()}"
        default_checklist = [
            {"item": "Physical Land Area and Boundary Wall Verification", "completed": False, "notes": ""},
            {"item": "Classrooms, Tutorial Rooms & Smart Labs Inspection", "completed": False, "notes": ""},
            {"item": "Central Library & Digital Learning Resources Audit", "completed": False, "notes": ""},
            {"item": "Fire Fighting & Safety Equipment Functional Check", "completed": False, "notes": ""},
            {"item": "Faculty Biometric Attendance & Salary Accounts Scrutiny", "completed": False, "notes": ""},
            {"item": "Barrier-Free Access (Ramps, Lifts, Toilets for Divyangjan)", "completed": False, "notes": ""}
        ]

        visit = EVCVisit(
            visit_reference=reference,
            application_id=application_id,
            institution_id=app.institution_id,
            proposed_date=proposed_date,
            confirmed_date=proposed_date,
            status=EVCStatus.SCHEDULED,
            assigned_officers=assigned_officers,
            coordinator_user_id=coordinator_user.id,
            preparation_checklist=default_checklist
        )
        db.add(visit)
        db.commit()
        db.refresh(visit)
        return visit

    @classmethod
    def update_checklist(
        cls,
        db: Session,
        visit_id: int,
        checklist: List[Dict[str, Any]]
    ) -> EVCVisit:
        visit = db.query(EVCVisit).filter(EVCVisit.id == visit_id).first()
        if not visit:
            raise HTTPException(status_code=404, detail="EVC visit not found")
        visit.preparation_checklist = checklist
        visit.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(visit)
        return visit

    @classmethod
    def submit_report(
        cls,
        db: Session,
        visit_id: int,
        visit_outcome: str,
        report_summary: str,
        deficiencies_found: List[str],
        follow_up_required: bool = False,
        file: Optional[UploadFile] = None
    ) -> EVCVisit:
        visit = db.query(EVCVisit).filter(EVCVisit.id == visit_id).first()
        if not visit:
            raise HTTPException(status_code=404, detail="EVC visit not found")

        report_file_path = None
        report_filename = None
        if file:
            filename = f"evc_report_{visit.visit_reference}_{uuid.uuid4().hex[:6]}.pdf"
            path = os.path.join(settings.STORAGE_DIR, filename)
            contents = file.file.read()
            with open(path, "wb") as f:
                f.write(contents)
            report_file_path = path
            report_filename = file.filename or filename

        visit.visit_outcome = visit_outcome
        visit.report_summary = report_summary
        visit.deficiencies_found = deficiencies_found
        visit.follow_up_required = follow_up_required
        if follow_up_required:
            visit.follow_up_deadline = datetime.datetime.utcnow() + datetime.timedelta(days=15)
        if report_file_path:
            visit.report_file_path = report_file_path
            visit.report_filename = report_filename

        visit.status = EVCStatus.COMPLETED
        visit.conducted_at = datetime.datetime.utcnow()
        visit.updated_at = datetime.datetime.utcnow()

        db.commit()
        db.refresh(visit)
        return visit
