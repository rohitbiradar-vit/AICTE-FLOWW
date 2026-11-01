import os
import uuid
import hashlib
import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.core.config import settings
from app.core.migration import reset_db_schema
from app.models.user import User, RoleEnum
from app.models.institution import Institution
from app.models.workflow import (
    WorkflowDefinition, WorkflowStage, WorkflowTransition,
    DeadlineRule, HolidayRule, StageKeys, ClockAttribution
)
from app.models.application import Application, StageHistory
from app.models.clock import ClockInterval, ClockPauseLog
from app.models.document import (
    Document, DocumentExtraction, DocumentValidationFinding, DocumentTypes
)
from app.models.scrutiny import ScrutinyReport, PriorityBands
from app.models.evc import EVCVisit, EVCStatus
from app.models.compliance import Undertaking, UndertakingStatus
from app.models.notification import Notification, NotificationType
from app.models.audit import AuditEvent
from app.services.ai_scrutiny_engine import AIScrutinyEngine
from make_clean_pdf import make_clean_pdf

DEMO_PASSWORD = "DemoPass123!"

def seed_database():
    print("Beginning AICTE FlowGuard database seeding...")

    # Recreate tables to ensure clean seed using Alembic migrations
    reset_db_schema()
    print("Database schema refreshed and migrated via Alembic.")

    db: Session = SessionLocal()
    try:

        # 1. Institutions
        apex = Institution(
            aicte_id="1-1002345678",
            name="Apex Institute of Engineering & Technology",
            institute_type="ENGINEERING_AND_TECHNOLOGY",
            region="Northern",
            state="Delhi",
            district="New Delhi",
            address="Plot 14, Knowledge Park III, Greater Noida, Delhi NCR - 201306",
            contact_email="principal@apex-tech.edu.in",
            contact_phone="+91-11-28945671",
            website="https://apex-tech.edu.in",
            status="ACTIVE"
        )
        saraswati = Institution(
            aicte_id="1-2003456789",
            name="Saraswati College of Architecture & Design",
            institute_type="ARCHITECTURE_AND_PLANNING",
            region="Western",
            state="Maharashtra",
            district="Pune",
            address="Survey No. 45, Viman Nagar, Pune, Maharashtra - 411014",
            contact_email="director@saraswati-arch.edu.in",
            contact_phone="+91-20-25678901",
            website="https://saraswati-arch.edu.in",
            status="ACTIVE"
        )
        greenfield = Institution(
            aicte_id="1-3004567890",
            name="Greenfield Institute of Pharmacy & Research",
            institute_type="PHARMACY",
            region="Southern",
            state="Karnataka",
            district="Bengaluru Urban",
            address="Electronic City Phase 1, Hosur Road, Bengaluru, Karnataka - 560100",
            contact_email="dean@greenfield-pharm.edu.in",
            contact_phone="+91-80-41238900",
            website="https://greenfield-pharm.edu.in",
            status="ACTIVE"
        )
        vidya = Institution(
            aicte_id="1-4005678901",
            name="Vidya Sagar Institute of Management Studies",
            institute_type="MANAGEMENT",
            region="Eastern",
            state="West Bengal",
            district="Kolkata",
            address="Sector V, Salt Lake City, Kolkata, West Bengal - 700091",
            contact_email="admin@vidyasagar-mgmt.edu.in",
            contact_phone="+91-33-23456789",
            website="https://vidyasagar-mgmt.edu.in",
            status="ACTIVE"
        )
        db.add_all([apex, saraswati, greenfield, vidya])
        db.flush()

        # 2. Users (Admin, Officials, Institutions)
        hashed_pw = hash_password(DEMO_PASSWORD)

        users = [
            # System Admin
            User(email="admin@flowguard.aicte.gov.in", password_hash=hashed_pw, full_name="Rajesh Sharma (Admin)", role=RoleEnum.ADMIN, designation="Chief System Administrator", region="Head Office"),
            # Officials
            User(email="scrutiny.officer@aicte.gov.in", password_hash=hashed_pw, full_name="Dr. Vikram Sen", role=RoleEnum.SCRUTINY_OFFICER, designation="Senior Scrutiny Officer", region="Northern"),
            User(email="evc.coordinator@aicte.gov.in", password_hash=hashed_pw, full_name="Prof. Sunita Rao", role=RoleEnum.EVC_COORDINATOR, designation="EVC Regional Coordinator", region="Northern"),
            User(email="doc.verifier@aicte.gov.in", password_hash=hashed_pw, full_name="Anil Kumar", role=RoleEnum.DOCUMENT_VERIFIER, designation="Statutory Document Verifier", region="Northern"),
            User(email="compliance.officer@aicte.gov.in", password_hash=hashed_pw, full_name="Pooja Deshmukh", role=RoleEnum.COMPLIANCE_OFFICER, designation="Compliance & Legal Officer", region="Northern"),
            User(email="regional.officer@aicte.gov.in", password_hash=hashed_pw, full_name="Dr. Harish Patel", role=RoleEnum.REGIONAL_OFFICER, designation="Regional Officer (North)", region="Northern"),
            User(email="bureau.authority@aicte.gov.in", password_hash=hashed_pw, full_name="Dr. K. N. Murthy", role=RoleEnum.BUREAU_AUTHORITY, designation="Advisor & Competent Authority (Regulation)", region="Head Office"),
            # Institutions
            User(email="institution@flowguard.aicte.gov.in", password_hash=hashed_pw, full_name="Dr. Alok Verma (Principal)", role=RoleEnum.INSTITUTION, designation="Principal", institution_id=apex.id),
            User(email="saraswati@flowguard.aicte.gov.in", password_hash=hashed_pw, full_name="Ar. Meera Joshi", role=RoleEnum.INSTITUTION, designation="Director", institution_id=saraswati.id),
            User(email="greenfield@flowguard.aicte.gov.in", password_hash=hashed_pw, full_name="Dr. Ramesh Hegde", role=RoleEnum.INSTITUTION, designation="Dean", institution_id=greenfield.id),
            User(email="vidya@flowguard.aicte.gov.in", password_hash=hashed_pw, full_name="Prof. S. K. Mukherjee", role=RoleEnum.INSTITUTION, designation="Director", institution_id=vidya.id),
        ]
        db.add_all(users)
        db.flush()

        # 3. Workflow Definition & Stages & Transitions
        wf = WorkflowDefinition(
            name="AICTE Integrated Institutional Approval Process 2026-27",
            code="APPROVAL_PROCESS_2026",
            description="Configurable state-machine workflow governing approval applications, automated scrutiny, EVC inspections, and competent authority approvals.",
            version="1.0",
            is_active=True
        )
        db.add(wf)
        db.flush()

        stages = [
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.DRAFT, stage_name="Draft Preparation", stage_order=1, sla_hours=168, clock_attribution=ClockAttribution.INSTITUTION, allowed_roles=[RoleEnum.INSTITUTION]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.SUBMITTED, stage_name="Submitted to Bureau", stage_order=2, sla_hours=48, clock_attribution=ClockAttribution.OFFICIAL, allowed_roles=[RoleEnum.SCRUTINY_OFFICER, RoleEnum.REGIONAL_OFFICER, RoleEnum.ADMIN]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.INITIAL_SCRUTINY, stage_name="Initial Scrutiny Review", stage_order=3, sla_hours=72, clock_attribution=ClockAttribution.OFFICIAL, allowed_roles=[RoleEnum.SCRUTINY_OFFICER, RoleEnum.REGIONAL_OFFICER]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.CLARIFICATION_REQUIRED, stage_name="Clarification Required", stage_order=4, sla_hours=120, clock_attribution=ClockAttribution.INSTITUTION, allowed_roles=[RoleEnum.INSTITUTION]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.RESUBMITTED, stage_name="Clarification Resubmitted", stage_order=5, sla_hours=48, clock_attribution=ClockAttribution.OFFICIAL, allowed_roles=[RoleEnum.SCRUTINY_OFFICER]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.FURTHER_REVIEW, stage_name="Further Scrutiny", stage_order=6, sla_hours=72, clock_attribution=ClockAttribution.OFFICIAL, allowed_roles=[RoleEnum.SCRUTINY_OFFICER, RoleEnum.REGIONAL_OFFICER]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.EVC_SCHEDULED, stage_name="EVC Visit Scheduled", stage_order=7, sla_hours=96, clock_attribution=ClockAttribution.OFFICIAL, allowed_roles=[RoleEnum.EVC_COORDINATOR, RoleEnum.REGIONAL_OFFICER]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.EVC_COMPLETED, stage_name="EVC Completed & Report Filed", stage_order=8, sla_hours=48, clock_attribution=ClockAttribution.OFFICIAL, allowed_roles=[RoleEnum.EVC_COORDINATOR, RoleEnum.REGIONAL_OFFICER]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.COMMITTEE_REVIEW, stage_name="Bureau Committee Review", stage_order=9, sla_hours=72, clock_attribution=ClockAttribution.OFFICIAL, allowed_roles=[RoleEnum.BUREAU_AUTHORITY, RoleEnum.REGIONAL_OFFICER]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.FINAL_APPROVAL, stage_name="Final Approval Granted", stage_order=10, sla_hours=0, clock_attribution=ClockAttribution.OFFICIAL, is_terminal=True, allowed_roles=[RoleEnum.BUREAU_AUTHORITY, RoleEnum.ADMIN]),
            WorkflowStage(workflow_id=wf.id, stage_key=StageKeys.REJECTED, stage_name="Application Rejected", stage_order=11, sla_hours=0, clock_attribution=ClockAttribution.OFFICIAL, is_terminal=True, allowed_roles=[RoleEnum.BUREAU_AUTHORITY, RoleEnum.ADMIN]),
        ]
        db.add_all(stages)
        db.flush()

        # Transitions
        transitions = [
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.DRAFT, to_stage_key=StageKeys.SUBMITTED,
                transition_name="Submit Application Dossier", allowed_roles=[RoleEnum.INSTITUTION, RoleEnum.ADMIN],
                prerequisites={"require_documents": [DocumentTypes.LAND_DEED, DocumentTypes.BUILDING_PLAN, DocumentTypes.FIRE_SAFETY_CERT, DocumentTypes.NOC_AFFILIATING_UNIVERSITY, DocumentTypes.FACULTY_LIST]}
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.SUBMITTED, to_stage_key=StageKeys.INITIAL_SCRUTINY,
                transition_name="Commence Scrutiny", allowed_roles=[RoleEnum.SCRUTINY_OFFICER, RoleEnum.REGIONAL_OFFICER, RoleEnum.ADMIN]
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.INITIAL_SCRUTINY, to_stage_key=StageKeys.CLARIFICATION_REQUIRED,
                transition_name="Return for Clarification", allowed_roles=[RoleEnum.SCRUTINY_OFFICER, RoleEnum.REGIONAL_OFFICER, RoleEnum.ADMIN],
                requires_reason=True
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.CLARIFICATION_REQUIRED, to_stage_key=StageKeys.RESUBMITTED,
                transition_name="Resubmit with Clarifications", allowed_roles=[RoleEnum.INSTITUTION, RoleEnum.ADMIN]
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.RESUBMITTED, to_stage_key=StageKeys.FURTHER_REVIEW,
                transition_name="Resume Scrutiny", allowed_roles=[RoleEnum.SCRUTINY_OFFICER, RoleEnum.REGIONAL_OFFICER, RoleEnum.ADMIN]
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.INITIAL_SCRUTINY, to_stage_key=StageKeys.EVC_SCHEDULED,
                transition_name="Refer to Expert Visiting Committee", allowed_roles=[RoleEnum.SCRUTINY_OFFICER, RoleEnum.EVC_COORDINATOR, RoleEnum.ADMIN]
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.FURTHER_REVIEW, to_stage_key=StageKeys.EVC_SCHEDULED,
                transition_name="Refer to Expert Visiting Committee", allowed_roles=[RoleEnum.SCRUTINY_OFFICER, RoleEnum.EVC_COORDINATOR, RoleEnum.ADMIN]
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.EVC_SCHEDULED, to_stage_key=StageKeys.EVC_COMPLETED,
                transition_name="Complete EVC Inspection", allowed_roles=[RoleEnum.EVC_COORDINATOR, RoleEnum.ADMIN]
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.EVC_COMPLETED, to_stage_key=StageKeys.COMMITTEE_REVIEW,
                transition_name="Forward to Bureau Committee", allowed_roles=[RoleEnum.EVC_COORDINATOR, RoleEnum.REGIONAL_OFFICER, RoleEnum.ADMIN],
                prerequisites={"require_evc_completed": True}
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.COMMITTEE_REVIEW, to_stage_key=StageKeys.FINAL_APPROVAL,
                transition_name="Grant AICTE Approval", allowed_roles=[RoleEnum.BUREAU_AUTHORITY, RoleEnum.ADMIN]
            ),
            WorkflowTransition(
                workflow_id=wf.id, from_stage_key=StageKeys.COMMITTEE_REVIEW, to_stage_key=StageKeys.REJECTED,
                transition_name="Reject Application", allowed_roles=[RoleEnum.BUREAU_AUTHORITY, RoleEnum.ADMIN],
                requires_reason=True
            ),
        ]
        db.add_all(transitions)

        # Holidays
        holidays = [
            HolidayRule(date=datetime.datetime(2026, 1, 26), name="Republic Day", is_recurring=True),
            HolidayRule(date=datetime.datetime(2026, 8, 15), name="Independence Day", is_recurring=True),
            HolidayRule(date=datetime.datetime(2026, 10, 2), name="Gandhi Jayanti", is_recurring=True),
        ]
        db.add_all(holidays)
        db.flush()

        # 4. Applications and Documents for the 5 Scenarios
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        now = datetime.datetime.utcnow()

        # SCENARIO 1: Complete Package (Standard Priority Score, < 25)
        app1 = Application(
            application_number="AICTE-2026-APEX-001",
            institution_id=apex.id,
            academic_year="2026-2027",
            application_type="EXTENSION_OF_APPROVAL",
            current_stage_key=StageKeys.INITIAL_SCRUTINY,
            declared_land_acres="5.0",
            declared_builtup_sqm="8500",
            declared_intake=480,
            declared_faculty_count=45,
            status="IN_PROGRESS",
            submitted_at=now - datetime.timedelta(days=2),
            current_deadline=now + datetime.timedelta(days=1),
            application_data={"program": "B.Tech Computer Science & Engineering", "courses_count": 6}
        )
        db.add(app1)
        db.flush()

        # Dual-clock intervals for app1
        # Draft (Institution): 3 days
        db.add(ClockInterval(
            application_id=app1.id, stage_key=StageKeys.DRAFT, clock_type=ClockAttribution.INSTITUTION,
            start_time=now - datetime.timedelta(days=5), end_time=now - datetime.timedelta(days=2),
            elapsed_seconds=259200.0, rule_version=settings.RULE_VERSION
        ))
        # Submitted -> Initial Scrutiny (Official): 2 days active
        db.add(ClockInterval(
            application_id=app1.id, stage_key=StageKeys.INITIAL_SCRUTINY, clock_type=ClockAttribution.OFFICIAL,
            start_time=now - datetime.timedelta(days=2), end_time=None,
            elapsed_seconds=0.0, rule_version=settings.RULE_VERSION
        ))

        # Documents for App 1
        doc_files_app1 = [
            (DocumentTypes.LAND_DEED, "Land_Title_Deed_Apex.pdf", [
                "Government of National Capital Territory of Delhi - Revenue Department",
                "Perpetual Registered Lease Deed & Ownership Title",
                "Institution: Apex Institute of Engineering & Technology",
                "Land Area: 5.0 Acres (Survey No. 104/A, Knowledge Park III)",
                "Date of Issue: 12/03/2018",
                "Valid up to: 12/03/2099",
                "Encumbrance: Clear and Unencumbered"
            ], datetime.datetime(2018, 3, 12), datetime.datetime(2099, 3, 12)),
            (DocumentTypes.BUILDING_PLAN, "Sanctioned_Building_Plan_Apex.pdf", [
                "Greater Noida Industrial Development Authority (GNIDA)",
                "Approved Architectural Blueprint & Master Plan",
                "Institution: Apex Institute of Engineering & Technology",
                "Built-up Area: 8500 Sq.Meters (Academic Block A, B & Workshops)",
                "Date of Issue: 15/06/2019",
                "Occupancy Status: Full Institutional Clearance"
            ], datetime.datetime(2019, 6, 15), None),
            (DocumentTypes.FIRE_SAFETY_CERT, "Fire_Safety_NOC_Apex.pdf", [
                "Delhi Fire Service Headquarters - Fire Safety Certificate",
                "Institution: Apex Institute of Engineering & Technology",
                "Date of Issue: 10/01/2025",
                "Valid up to: 10/01/2028",
                "Clearance: Hydrant, Smoke Detection & Emergency Stairwells Certified"
            ], datetime.datetime(2025, 1, 10), datetime.datetime(2028, 1, 10)),
            (DocumentTypes.NOC_AFFILIATING_UNIVERSITY, "University_Affiliation_NOC_Apex.pdf", [
                "Dr. A.P.J. Abdul Kalam Technical University (AKTU)",
                "Letter of Permanent Academic Affiliation",
                "Institution: Apex Institute of Engineering & Technology",
                "Date of Issue: 20/07/2024",
                "Approved Intake: 480 Seats across 6 Engineering Disciplines"
            ], datetime.datetime(2024, 7, 20), None),
            (DocumentTypes.FACULTY_LIST, "Approved_Faculty_Roster_Apex.pdf", [
                "Apex Institute of Engineering & Technology - Office of the Dean",
                "Statutory Faculty Roster complying with AICTE Cadre Ratio (1:20)",
                "Total Faculty: 45 Full-time Ph.D. and M.Tech Educators",
                "Date of Issue: 01/02/2026"
            ], datetime.datetime(2026, 2, 1), None)
        ]

        for dtype, fname, lines, is_dt, exp_dt in doc_files_app1:
            doc_uuid = str(uuid.uuid4())
            storage_path = os.path.join(settings.STORAGE_DIR, f"{doc_uuid}_{fname}")
            make_clean_pdf(storage_path, lines)
            contents = open(storage_path, "rb").read()
            doc_rec = Document(
                document_uuid=doc_uuid, institution_id=apex.id, application_id=app1.id,
                document_type=dtype, title=fname.replace("_", " ").replace(".pdf", ""),
                original_filename=fname, storage_filename=os.path.basename(storage_path),
                file_path=storage_path, file_size_bytes=len(contents), mime_type="application/pdf",
                sha256_hash=hashlib.sha256(contents).hexdigest(), version=1, is_current=True,
                issue_date=is_dt, expiry_date=exp_dt, requires_renewal=bool(exp_dt),
                verification_status="VERIFIED"
            )
            db.add(doc_rec)
            db.flush()
            AIScrutinyEngine.extract_document_fields(db, doc_rec)

        # Generate Scrutiny Report for App 1
        AIScrutinyEngine.generate_scrutiny_report(db, app1.id)

        # SCENARIO 2: Inconsistency (Land Area Mismatch, Enhanced Priority Score)
        app2 = Application(
            application_number="AICTE-2026-SARA-002",
            institution_id=saraswati.id,
            academic_year="2026-2027",
            application_type="NEW_PROGRAMME",
            current_stage_key=StageKeys.INITIAL_SCRUTINY,
            declared_land_acres="7.5",  # Mismatch with deed!
            declared_builtup_sqm="6000",
            declared_intake=120,
            status="IN_PROGRESS",
            submitted_at=now - datetime.timedelta(days=1),
            current_deadline=now + datetime.timedelta(days=2)
        )
        db.add(app2)
        db.flush()

        db.add(ClockInterval(
            application_id=app2.id, stage_key=StageKeys.INITIAL_SCRUTINY, clock_type=ClockAttribution.OFFICIAL,
            start_time=now - datetime.timedelta(days=1), end_time=None,
            elapsed_seconds=0.0, rule_version=settings.RULE_VERSION
        ))

        doc_files_app2 = [
            (DocumentTypes.LAND_DEED, "Land_Deed_Saraswati.pdf", [
                "Government of Maharashtra - Registration and Stamps Department",
                "Institution: Saraswati College of Architecture & Design",
                "Land Area: 5.0 Acres (Viman Nagar, Pune)",
                "Date of Issue: 18/04/2021",
                "Valid up to: 18/04/2050"
            ], datetime.datetime(2021, 4, 18), datetime.datetime(2050, 4, 18)),
            (DocumentTypes.BUILDING_PLAN, "Building_Plan_Saraswati.pdf", [
                "Pune Municipal Corporation Town Planning Wing",
                "Institution: Saraswati College of Architecture & Design",
                "Built-up Area: 6000 Sq.Meters",
                "Date of Issue: 22/05/2021"
            ], datetime.datetime(2021, 5, 22), None),
            (DocumentTypes.FIRE_SAFETY_CERT, "Fire_NOC_Saraswati.pdf", [
                "Pune Metropolitan Region Fire Authority",
                "Institution: Saraswati College of Architecture & Design",
                "Date of Issue: 10/11/2024",
                "Valid up to: 10/11/2027"
            ], datetime.datetime(2024, 11, 10), datetime.datetime(2027, 11, 10)),
            (DocumentTypes.NOC_AFFILIATING_UNIVERSITY, "Affiliation_SavitribaiPhulePuneUniv.pdf", [
                "Savitribai Phule Pune University",
                "Institution: Saraswati College of Architecture & Design",
                "Date of Issue: 14/06/2025"
            ], datetime.datetime(2025, 6, 14), None),
            (DocumentTypes.FACULTY_LIST, "Faculty_Roster_Saraswati.pdf", [
                "Institution: Saraswati College of Architecture & Design",
                "Total Faculty: 18 Council of Architecture Registered Architects",
                "Date of Issue: 10/01/2026"
            ], datetime.datetime(2026, 1, 10), None)
        ]

        for dtype, fname, lines, is_dt, exp_dt in doc_files_app2:
            doc_uuid = str(uuid.uuid4())
            storage_path = os.path.join(settings.STORAGE_DIR, f"{doc_uuid}_{fname}")
            make_clean_pdf(storage_path, lines)
            contents = open(storage_path, "rb").read()
            doc_rec = Document(
                document_uuid=doc_uuid, institution_id=saraswati.id, application_id=app2.id,
                document_type=dtype, title=fname.replace("_", " ").replace(".pdf", ""),
                original_filename=fname, storage_filename=os.path.basename(storage_path),
                file_path=storage_path, file_size_bytes=len(contents), mime_type="application/pdf",
                sha256_hash=hashlib.sha256(contents).hexdigest(), version=1, is_current=True,
                issue_date=is_dt, expiry_date=exp_dt, requires_renewal=bool(exp_dt),
                verification_status="PENDING"
            )
            db.add(doc_rec)
            db.flush()
            AIScrutinyEngine.extract_document_fields(db, doc_rec)

        AIScrutinyEngine.generate_scrutiny_report(db, app2.id)

        # SCENARIO 3: Missing Required Document & Expired Fire Safety (High Priority Score, 75+)
        app3 = Application(
            application_number="AICTE-2026-GREN-003",
            institution_id=greenfield.id,
            academic_year="2026-2027",
            application_type="EXTENSION_OF_APPROVAL",
            current_stage_key=StageKeys.SUBMITTED,
            declared_land_acres="3.5",
            declared_builtup_sqm="4200",
            declared_intake=100,
            status="IN_PROGRESS",
            submitted_at=now - datetime.timedelta(hours=18),
            current_deadline=now + datetime.timedelta(hours=30)
        )
        db.add(app3)
        db.flush()

        db.add(ClockInterval(
            application_id=app3.id, stage_key=StageKeys.SUBMITTED, clock_type=ClockAttribution.OFFICIAL,
            start_time=now - datetime.timedelta(hours=18), end_time=None,
            elapsed_seconds=0.0, rule_version=settings.RULE_VERSION
        ))

        # Missing University NOC! And Expired Fire Certificate (expired in 2024)
        doc_files_app3 = [
            (DocumentTypes.LAND_DEED, "Land_Document_Greenfield.pdf", [
                "Government of Karnataka - Department of Stamps and Registration",
                "Institution: Greenfield Institute of Pharmacy & Research",
                "Land Area: 3.5 Acres",
                "Date of Issue: 05/02/2020",
                "Valid up to: 05/02/2045"
            ], datetime.datetime(2020, 2, 5), datetime.datetime(2045, 2, 5)),
            (DocumentTypes.BUILDING_PLAN, "Floor_Plan_Greenfield.pdf", [
                "Karnataka Industrial Areas Development Board (KIADB)",
                "Institution: Greenfield Institute of Pharmacy & Research",
                "Built-up Area: 4200 Sq.Meters",
                "Date of Issue: 18/08/2020"
            ], datetime.datetime(2020, 8, 18), None),
            (DocumentTypes.FIRE_SAFETY_CERT, "Fire_NOC_Expired_Greenfield.pdf", [
                "Karnataka State Fire and Emergency Services",
                "Institution: Greenfield Institute of Pharmacy & Research",
                "Date of Issue: 15/03/2021",
                "Valid up to: 15/03/2024"  # EXPIRED!
            ], datetime.datetime(2021, 3, 15), datetime.datetime(2024, 3, 15)),
            (DocumentTypes.FACULTY_LIST, "Pharmacy_Faculty_Greenfield.pdf", [
                "Institution: Greenfield Institute of Pharmacy & Research",
                "Total Faculty: 16 M.Pharm / Ph.D. Faculty",
                "Date of Issue: 01/01/2026"
            ], datetime.datetime(2026, 1, 1), None)
            # Notice: NOC_AFFILIATING_UNIVERSITY is missing!
        ]

        for dtype, fname, lines, is_dt, exp_dt in doc_files_app3:
            doc_uuid = str(uuid.uuid4())
            storage_path = os.path.join(settings.STORAGE_DIR, f"{doc_uuid}_{fname}")
            make_clean_pdf(storage_path, lines)
            contents = open(storage_path, "rb").read()
            doc_rec = Document(
                document_uuid=doc_uuid, institution_id=greenfield.id, application_id=app3.id,
                document_type=dtype, title=fname.replace("_", " ").replace(".pdf", ""),
                original_filename=fname, storage_filename=os.path.basename(storage_path),
                file_path=storage_path, file_size_bytes=len(contents), mime_type="application/pdf",
                sha256_hash=hashlib.sha256(contents).hexdigest(), version=1, is_current=True,
                issue_date=is_dt, expiry_date=exp_dt, requires_renewal=bool(exp_dt),
                verification_status="PENDING"
            )
            db.add(doc_rec)
            db.flush()
            AIScrutinyEngine.extract_document_fields(db, doc_rec)

        AIScrutinyEngine.generate_scrutiny_report(db, app3.id)

        # SCENARIO 4: Application in Clarification Required (Institution Clock Active)
        app4 = Application(
            application_number="AICTE-2026-VIDY-004",
            institution_id=vidya.id,
            academic_year="2026-2027",
            application_type="INCREASE_INTAKE",
            current_stage_key=StageKeys.CLARIFICATION_REQUIRED,
            declared_land_acres="2.0",
            declared_builtup_sqm="3500",
            declared_intake=180,
            status="IN_PROGRESS",
            clarification_notes="Scrutiny deficiency: Submit revised audited balance sheet and occupancy certificate for the newly constructed MBA executive block.",
            submitted_at=now - datetime.timedelta(days=7),
            current_deadline=now + datetime.timedelta(days=3)
        )
        db.add(app4)
        db.flush()

        # Prior official interval completed, now Institution Clock active
        db.add(ClockInterval(
            application_id=app4.id, stage_key=StageKeys.INITIAL_SCRUTINY, clock_type=ClockAttribution.OFFICIAL,
            start_time=now - datetime.timedelta(days=7), end_time=now - datetime.timedelta(days=2),
            elapsed_seconds=432000.0, rule_version=settings.RULE_VERSION
        ))
        db.add(ClockInterval(
            application_id=app4.id, stage_key=StageKeys.CLARIFICATION_REQUIRED, clock_type=ClockAttribution.INSTITUTION,
            start_time=now - datetime.timedelta(days=2), end_time=None,
            elapsed_seconds=0.0, rule_version=settings.RULE_VERSION
        ))

        # SCENARIO 5: EVC Scheduled (Expert Visiting Committee in progress)
        app5 = Application(
            application_number="AICTE-2026-APEX-005",
            institution_id=apex.id,
            academic_year="2026-2027",
            application_type="INCREASE_INTAKE",
            current_stage_key=StageKeys.EVC_SCHEDULED,
            declared_land_acres="5.0",
            declared_builtup_sqm="8500",
            declared_intake=600,
            status="IN_PROGRESS",
            submitted_at=now - datetime.timedelta(days=12),
            current_deadline=now + datetime.timedelta(days=2)
        )
        db.add(app5)
        db.flush()

        db.add(ClockInterval(
            application_id=app5.id, stage_key=StageKeys.EVC_SCHEDULED, clock_type=ClockAttribution.OFFICIAL,
            start_time=now - datetime.timedelta(days=2), end_time=None,
            elapsed_seconds=0.0, rule_version=settings.RULE_VERSION
        ))

        # EVC Visit scheduled for app5
        evc_visit = EVCVisit(
            visit_reference="EVC-2026-DEL-041",
            application_id=app5.id,
            institution_id=apex.id,
            proposed_date=now + datetime.timedelta(days=3),
            confirmed_date=now + datetime.timedelta(days=3),
            status=EVCStatus.SCHEDULED,
            assigned_officers=[
                {"name": "Prof. R. C. Mathur", "designation": "Committee Chairman (IIT Delhi)", "email": "rcmathur@iitd.ac.in"},
                {"name": "Dr. Sneha Pillai", "designation": "AICTE Expert Member (NIT)", "email": "spillai@nit.ac.in"},
                {"name": "Prof. Sunita Rao", "designation": "Regional EVC Coordinator", "email": "evc.coordinator@aicte.gov.in"}
            ],
            coordinator_user_id=users[2].id, # evc.coordinator
            preparation_checklist=[
                {"item": "Physical Land Area and Boundary Wall Verification", "completed": True, "notes": "Fencing verified via GPS boundary."},
                {"item": "Classrooms, Tutorial Rooms & Smart Labs Inspection", "completed": True, "notes": "6 smart lecture halls verified."},
                {"item": "Central Library & Digital Learning Resources Audit", "completed": False, "notes": "Checking e-journal subscription licenses."},
                {"item": "Fire Fighting & Safety Equipment Functional Check", "completed": False, "notes": "Pressure testing of fire hydrants."},
                {"item": "Faculty Biometric Attendance & Salary Accounts Scrutiny", "completed": False, "notes": "Bank transfer statements pending review."},
                {"item": "Barrier-Free Access (Ramps, Lifts, Toilets for Divyangjan)", "completed": True, "notes": "Wheelchair ramps in place."}
            ]
        )
        db.add(evc_visit)

        # SCENARIO 6: Final Approval Granted & Active Compliance Undertakings
        app6 = Application(
            application_number="AICTE-2026-APEX-006",
            institution_id=apex.id,
            academic_year="2025-2026",
            application_type="EXTENSION_OF_APPROVAL",
            current_stage_key=StageKeys.FINAL_APPROVAL,
            status="APPROVED",
            submitted_at=now - datetime.timedelta(days=60),
            updated_at=now - datetime.timedelta(days=30)
        )
        db.add(app6)
        db.flush()

        # Undertakings for Apex
        ut1 = Undertaking(
            undertaking_code="UT-2026-APEX-01",
            institution_id=apex.id,
            application_id=app6.id,
            title="Installation of Sewage Treatment Plant (STP) & Solar Grid",
            requirement_clause="AICTE APH 2026-27 Ch. 3 Cl. 14 (Green Campus Mandate)",
            description="Institution undertook to commission a 50 KLD STP unit and 25 kW rooftop solar grid within 90 days of approval.",
            due_date=now - datetime.timedelta(days=5), # Overdue!
            status=UndertakingStatus.OVERDUE,
            requires_annual_renewal=False
        )
        ut2 = Undertaking(
            undertaking_code="UT-2026-APEX-02",
            institution_id=apex.id,
            application_id=app6.id,
            title="Divyangjan Elevator & Tactile Pathway Compliance",
            requirement_clause="AICTE APH 2026-27 Ch. 3 Cl. 8 (Accessibility Guidelines)",
            description="Submission of completion certificate for dedicated lift in Academic Block B.",
            due_date=now + datetime.timedelta(days=20),
            status=UndertakingStatus.SUBMITTED,
            evidence_filename="Lift_Completion_Certificate_Apex.pdf",
            evidence_description="Lift inspection and safety certificate issued by PWD Electrical Inspectorate.",
            submitted_at=now - datetime.timedelta(days=1),
            requires_annual_renewal=True
        )
        db.add_all([ut1, ut2])

        # Notifications
        notifs = [
            Notification(
                user_id=users[7].id, # institution user (apex)
                title="CRITICAL: Compliance Undertaking Overdue",
                message="Undertaking UT-2026-APEX-01 (Sewage Treatment Plant & Solar Grid) is past its due date. Upload evidence immediately.",
                notification_type=NotificationType.OVERDUE,
                severity="CRITICAL",
                action_link="/institution/compliance",
                due_at=now - datetime.timedelta(days=5)
            ),
            Notification(
                user_id=users[1].id, # scrutiny officer
                title="High Scrutiny Alert: Application #AICTE-2026-GREN-003",
                message="Application #AICTE-2026-GREN-003 generated High Priority Score (75) due to missing University NOC and expired Fire Safety Certificate.",
                notification_type=NotificationType.DEADLINE,
                severity="CRITICAL",
                related_application_id=app3.id,
                action_link=f"/official/applications/{app3.id}"
            ),
            Notification(
                user_id=users[10].id, # vidya institution user
                title="Clarification Required for Application #AICTE-2026-VIDY-004",
                message="Scrutiny deficiency: Submit revised audited balance sheet and occupancy certificate for executive block.",
                notification_type=NotificationType.CLARIFICATION,
                severity="WARNING",
                related_application_id=app4.id,
                action_link=f"/institution/applications/{app4.id}"
            ),
        ]
        db.add_all(notifs)

        # Audit events
        audit1 = AuditEvent(
            user_id=users[0].id, user_email="admin@flowguard.aicte.gov.in",
            action="SYSTEM_INIT", entity_type="WORKFLOW", entity_id=wf.id,
            details={"rule_version": settings.RULE_VERSION, "status": "INITIALIZED"}
        )
        audit2 = AuditEvent(
            user_id=users[7].id, user_email="institution@flowguard.aicte.gov.in",
            action="STAGE_TRANSITION", entity_type="APPLICATION", entity_id=app1.id,
            details={"from": "DRAFT", "to": "SUBMITTED"}
        )
        db.add_all([audit1, audit2])

        db.commit()
        print("AICTE FlowGuard database seeded successfully with rich synthetic regulatory data!")

    except Exception as e:
        db.rollback()
        print(f"Error during database seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
