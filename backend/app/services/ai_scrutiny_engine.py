import os
import re
import uuid
import hashlib
import datetime
from typing import Dict, Any, List, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from pypdf import PdfReader
from app.core.config import settings
from app.models.document import (
    Document, DocumentExtraction, DocumentValidationFinding, DocumentTypes
)
from app.models.application import Application
from app.models.scrutiny import ScrutinyReport, PriorityBands
from app.models.user import User

class AIScrutinyEngine:
    MANDATORY_DOCS = [
        DocumentTypes.LAND_DEED,
        DocumentTypes.BUILDING_PLAN,
        DocumentTypes.FIRE_SAFETY_CERT,
        DocumentTypes.NOC_AFFILIATING_UNIVERSITY,
        DocumentTypes.FACULTY_LIST
    ]

    # --- Step 1: Secure Ingestion ---
    @classmethod
    def ingest_document(
        cls,
        db: Session,
        file: UploadFile,
        document_type: str,
        institution_id: int,
        application_id: Optional[int],
        user: User,
        title: Optional[str] = None
    ) -> Document:
        # Validate MIME type
        if file.content_type not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{file.content_type}'. Allowed types: {settings.ALLOWED_MIME_TYPES}"
            )

        # Read file bytes & validate size
        contents = file.file.read()
        file_size = len(contents)
        if file_size > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum permitted limit ({settings.MAX_FILE_SIZE_BYTES / (1024*1024)} MB)"
            )

        # Validate magic numbers (PDF: %PDF, PNG: \x89PNG, JPEG: \xff\xd8\xff)
        is_valid_signature = False
        if contents.startswith(b"%PDF"):
            is_valid_signature = True
        elif contents.startswith(b"\x89PNG"):
            is_valid_signature = True
        elif contents.startswith(b"\xff\xd8\xff"):
            is_valid_signature = True

        if not is_valid_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match declared MIME signature."
            )

        # Generate sha256 hash
        sha256 = hashlib.sha256(contents).hexdigest()

        # Check existing version for this document_type
        existing_doc = db.query(Document).filter(
            Document.institution_id == institution_id,
            Document.application_id == application_id,
            Document.document_type == document_type,
            Document.is_current == True
        ).first()

        version = 1
        if existing_doc:
            version = existing_doc.version + 1
            existing_doc.is_current = False

        # Generate server-controlled private storage path
        doc_uuid = str(uuid.uuid4())
        ext = os.path.splitext(file.filename or "")[1] or ".pdf"
        storage_filename = f"{doc_uuid}_v{version}{ext}"
        storage_path = os.path.join(settings.STORAGE_DIR, storage_filename)

        with open(storage_path, "wb") as f:
            f.write(contents)

        doc = Document(
            document_uuid=doc_uuid,
            institution_id=institution_id,
            application_id=application_id,
            document_type=document_type,
            title=title or (file.filename or document_type),
            original_filename=file.filename or storage_filename,
            storage_filename=storage_filename,
            file_path=storage_path,
            file_size_bytes=file_size,
            mime_type=file.content_type,
            sha256_hash=sha256,
            version=version,
            is_current=True,
            verification_status="PENDING",
            uploaded_by_user_id=user.id
        )
        db.add(doc)
        db.flush()

        # Run extraction immediately
        cls.extract_document_fields(db, doc)

        return doc

    # --- Step 2: Extraction ---
    @classmethod
    def extract_document_fields(cls, db: Session, doc: Document) -> DocumentExtraction:
        raw_text = ""
        page_count = 1
        extracted_fields: Dict[str, Any] = {}
        confidence_scores: Dict[str, float] = {}

        if doc.mime_type == "application/pdf":
            try:
                reader = PdfReader(doc.file_path)
                page_count = len(reader.pages)
                for page_idx, page in enumerate(reader.pages):
                    t = page.extract_text() or ""
                    raw_text += f"\n--- Page {page_idx+1} ---\n" + t
            except Exception as e:
                raw_text = f"Text extraction error: {str(e)}"
        else:
            raw_text = f"[Image/scanned format: {doc.original_filename}]"

        # Deterministic regex field extractors
        # 1. Institution Name
        inst_match = re.search(r"(?:Institution|College|Institute|University|Trust)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]{5,80})", raw_text, re.IGNORECASE)
        if inst_match:
            extracted_fields["institution_name"] = inst_match.group(1).strip()
            confidence_scores["institution_name"] = 0.92
        else:
            extracted_fields["institution_name"] = None
            confidence_scores["institution_name"] = 0.0

        # 2. Land Area (Acres or Sq Meters)
        land_match = re.search(r"(?:Land\s+Area|Total\s+Land|Plot\s+Area)\s*[:\-]?\s*([0-9\.]+)\s*(Acres?|Sq\.?\s*Meters?|Hectares?)", raw_text, re.IGNORECASE)
        if land_match:
            extracted_fields["land_area"] = f"{land_match.group(1)} {land_match.group(2)}"
            confidence_scores["land_area"] = 0.95
        else:
            extracted_fields["land_area"] = None
            confidence_scores["land_area"] = 0.0

        # 3. Built-Up Area
        built_match = re.search(r"(?:Built[-\s]up\s+Area|Constructed\s+Area|Plinth\s+Area)\s*[:\-]?\s*([0-9\.]+)\s*(Sq\.?\s*Meters?|Sq\.?\s*Ft\.?)", raw_text, re.IGNORECASE)
        if built_match:
            extracted_fields["built_up_area"] = f"{built_match.group(1)} {built_match.group(2)}"
            confidence_scores["built_up_area"] = 0.90
        else:
            extracted_fields["built_up_area"] = None
            confidence_scores["built_up_area"] = 0.0

        # 4. Dates: Issue Date & Expiry Date
        issue_match = re.search(r"(?:Date\s+of\s+Issue|Issue\s+Date|Date|Dated)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", raw_text, re.IGNORECASE)
        if issue_match:
            extracted_fields["issue_date_str"] = issue_match.group(1)
            confidence_scores["issue_date"] = 0.88
            parsed_issue = cls._parse_date(issue_match.group(1))
            if parsed_issue:
                doc.issue_date = parsed_issue

        expiry_match = re.search(r"(?:Valid\s+(?:up\s+to|till|until)|Expiry\s+Date|Date\s+of\s+Expiry)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", raw_text, re.IGNORECASE)
        if expiry_match:
            extracted_fields["expiry_date_str"] = expiry_match.group(1)
            confidence_scores["expiry_date"] = 0.91
            parsed_exp = cls._parse_date(expiry_match.group(1))
            if parsed_exp:
                doc.expiry_date = parsed_exp
                doc.requires_renewal = True

        # 5. Intake Capacity / Faculty Count
        intake_match = re.search(r"(?:Sanctioned\s+Intake|Approved\s+Intake|Total\s+Intake)\s*[:\-]?\s*(\d{2,4})", raw_text, re.IGNORECASE)
        if intake_match:
            extracted_fields["approved_intake"] = int(intake_match.group(1))
            confidence_scores["approved_intake"] = 0.94

        faculty_match = re.search(r"(?:Total\s+Faculty|Teaching\s+Staff|Faculty\s+Count)\s*[:\-]?\s*(\d{1,3})", raw_text, re.IGNORECASE)
        if faculty_match:
            extracted_fields["faculty_count"] = int(faculty_match.group(1))
            confidence_scores["faculty_count"] = 0.89

        # Overall confidence
        valid_scores = [s for s in confidence_scores.values() if s > 0]
        overall_conf = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.5

        # Snippet preview
        preview_clean = raw_text[:500].replace("\n", " ").strip()

        extraction = DocumentExtraction(
            document_id=doc.id,
            extraction_method="DIGITAL_TEXT_AND_RULE_PARSER",
            extracted_text_preview=preview_clean,
            extracted_fields=extracted_fields,
            confidence_scores=confidence_scores,
            overall_confidence=overall_conf,
            processing_status="COMPLETED",
            page_count=page_count
        )
        db.add(extraction)
        db.flush()
        return extraction

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime.datetime]:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y"):
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    # --- Step 3 & 4: Rule-based Verification & Scrutiny Report Generation ---
    @classmethod
    def generate_scrutiny_report(cls, db: Session, application_id: int) -> ScrutinyReport:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        docs = db.query(Document).filter(
            Document.application_id == application_id,
            Document.is_current == True
        ).all()

        document_inventory = []
        uploaded_doc_types = set()
        extracted_summary: Dict[str, Any] = {}
        missing_evidence: List[Dict[str, Any]] = []
        inconsistencies: List[Dict[str, Any]] = []
        expiry_findings: List[Dict[str, Any]] = []
        low_confidence_extractions: List[Dict[str, Any]] = []
        findings_requiring_human_review: List[Dict[str, Any]] = []
        rules_checked: List[Dict[str, Any]] = []
        suggested_actions: List[str] = []

        now = datetime.datetime.utcnow()

        for doc in docs:
            uploaded_doc_types.add(doc.document_type)
            ext = db.query(DocumentExtraction).filter(DocumentExtraction.document_id == doc.id).first()
            fields = ext.extracted_fields if ext else {}
            conf = ext.confidence_scores if ext else {}

            document_inventory.append({
                "document_id": doc.id,
                "document_uuid": doc.document_uuid,
                "document_type": doc.document_type,
                "title": doc.title,
                "version": doc.version,
                "file_size_kb": round(doc.file_size_bytes / 1024, 1),
                "sha256_hash": doc.sha256_hash[:12] + "...",
                "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
                "verification_status": doc.verification_status,
                "overall_confidence": ext.overall_confidence if ext else 0.5
            })

            # Check low confidence
            if ext and ext.overall_confidence < 0.70:
                low_conf_finding = {
                    "document_type": doc.document_type,
                    "title": doc.title,
                    "confidence": ext.overall_confidence,
                    "issue": f"Extraction confidence is low ({ext.overall_confidence * 100}%). Manual inspection of source document required.",
                    "source_reference": f"{doc.original_filename} (p. 1)"
                }
                low_confidence_extractions.append(low_conf_finding)
                findings_requiring_human_review.append(low_conf_finding)

            # Check expiry
            if doc.expiry_date:
                if doc.expiry_date < now:
                    exp_finding = {
                        "document_type": doc.document_type,
                        "title": doc.title,
                        "expiry_date": doc.expiry_date.strftime("%d-%b-%Y"),
                        "severity": "CRITICAL",
                        "issue": f"Document expired on {doc.expiry_date.strftime('%d-%b-%Y')}. Valid statutory renewal required.",
                        "source_reference": f"{doc.original_filename}"
                    }
                    expiry_findings.append(exp_finding)
                elif doc.expiry_date < now + datetime.timedelta(days=90):
                    exp_finding = {
                        "document_type": doc.document_type,
                        "title": doc.title,
                        "expiry_date": doc.expiry_date.strftime("%d-%b-%Y"),
                        "severity": "WARNING",
                        "issue": f"Document expires within 90 days ({doc.expiry_date.strftime('%d-%b-%Y')}). Institution must provide undertaking for renewal.",
                        "source_reference": f"{doc.original_filename}"
                    }
                    expiry_findings.append(exp_finding)

            # Check cross document fields
            if doc.document_type == DocumentTypes.LAND_DEED and fields.get("land_area"):
                extracted_summary["land_area_extracted"] = fields["land_area"]
                # Cross-check with declared land acres in application
                if application.declared_land_acres:
                    declared = float(re.findall(r"[\d\.]+", application.declared_land_acres)[0]) if re.findall(r"[\d\.]+", application.declared_land_acres) else 0.0
                    extracted_num = float(re.findall(r"[\d\.]+", fields["land_area"])[0]) if re.findall(r"[\d\.]+", fields["land_area"]) else 0.0
                    if abs(declared - extracted_num) > 0.05:
                        mismatch = {
                            "field": "Land Area",
                            "declared_in_application": f"{application.declared_land_acres} Acres",
                            "extracted_from_document": fields["land_area"],
                            "document": doc.original_filename,
                            "severity": "HIGH",
                            "issue": "Declared land area differs from extracted land deed area. Scrutiny officer must verify whether additional plots are leased.",
                            "source_reference": f"{doc.original_filename} (p. 1)"
                        }
                        inconsistencies.append(mismatch)
                        findings_requiring_human_review.append(mismatch)

            if doc.document_type == DocumentTypes.BUILDING_PLAN and fields.get("built_up_area"):
                extracted_summary["built_up_area_extracted"] = fields["built_up_area"]
                if application.declared_builtup_sqm:
                    declared_b = float(re.findall(r"[\d\.]+", application.declared_builtup_sqm)[0]) if re.findall(r"[\d\.]+", application.declared_builtup_sqm) else 0.0
                    extracted_b = float(re.findall(r"[\d\.]+", fields["built_up_area"])[0]) if re.findall(r"[\d\.]+", fields["built_up_area"]) else 0.0
                    if abs(declared_b - extracted_b) > 50.0: # allow minor difference
                        mismatch = {
                            "field": "Built-up Area",
                            "declared_in_application": f"{application.declared_builtup_sqm} Sq.m",
                            "extracted_from_document": fields["built_up_area"],
                            "document": doc.original_filename,
                            "severity": "MEDIUM",
                            "issue": "Declared built-up area differs from architectural building plan.",
                            "source_reference": f"{doc.original_filename} (p. 1)"
                        }
                        inconsistencies.append(mismatch)
                        findings_requiring_human_review.append(mismatch)

        # 3b. Check missing mandatory documents
        for req_doc in cls.MANDATORY_DOCS:
            rules_checked.append({
                "rule": f"Mandatory Document: {req_doc}",
                "status": "PASSED" if req_doc in uploaded_doc_types else "FAILED"
            })
            if req_doc not in uploaded_doc_types:
                missing_finding = {
                    "document_type": req_doc,
                    "severity": "CRITICAL",
                    "issue": f"Mandatory regulatory document '{req_doc.replace('_', ' ')}' is not uploaded.",
                    "regulatory_clause": "AICTE Approval Process Handbook (APH) 2026-27 Mandatory Checklist Item"
                }
                missing_evidence.append(missing_finding)
                findings_requiring_human_review.append(missing_finding)

        # 3c. Rule Checks Summary
        rules_checked.append({"rule": "Fire Safety Certificate Active Validity", "status": "FAILED" if any(e["document_type"] == DocumentTypes.FIRE_SAFETY_CERT for e in expiry_findings if e["severity"] == "CRITICAL") else "PASSED"})
        rules_checked.append({"rule": "Land Deed Area Consistency", "status": "FAILED" if any(i["field"] == "Land Area" for i in inconsistencies) else "PASSED"})
        rules_checked.append({"rule": "Affiliating University NOC Present", "status": "PASSED" if DocumentTypes.NOC_AFFILIATING_UNIVERSITY in uploaded_doc_types else "FAILED"})

        # --- Step 5: Explainable Scrutiny Priority Score Calculation ---
        # Formula:
        # Base: 0
        # +25 per missing mandatory document (cap at 50)
        # +20 per cross-document mismatch (cap at 40)
        # +20 per expired document (cap at 40)
        # +10 per low confidence extraction (cap at 20)
        missing_doc_pts = min(50, len(missing_evidence) * 25)
        inconsistency_pts = min(40, len(inconsistencies) * 20)
        expired_doc_pts = min(40, len([e for e in expiry_findings if e["severity"] == "CRITICAL"]) * 20)
        low_conf_pts = min(20, len(low_confidence_extractions) * 10)

        raw_score = missing_doc_pts + inconsistency_pts + expired_doc_pts + low_conf_pts
        priority_score = min(100, raw_score)

        if priority_score <= 24:
            priority_band = PriorityBands.STANDARD
        elif priority_score <= 74:
            priority_band = PriorityBands.ENHANCED
        else:
            priority_band = PriorityBands.HIGH

        score_formula_breakdown = {
            "final_score": priority_score,
            "band": priority_band,
            "formula": "priority_score = min(100, missing_doc_pts + inconsistency_pts + expired_doc_pts + low_conf_pts)",
            "factor_contributions": [
                {
                    "factor": "Missing Mandatory Documents",
                    "weight_per_item": 25,
                    "item_count": len(missing_evidence),
                    "points": missing_doc_pts,
                    "explanation": f"{len(missing_evidence)} mandatory document(s) missing from submitted application dossier."
                },
                {
                    "factor": "Cross-Document Inconsistencies",
                    "weight_per_item": 20,
                    "item_count": len(inconsistencies),
                    "points": inconsistency_pts,
                    "explanation": f"{len(inconsistencies)} data mismatch(es) detected between application declaration and extracted certificates."
                },
                {
                    "factor": "Expired Documents",
                    "weight_per_item": 20,
                    "item_count": len([e for e in expiry_findings if e["severity"] == "CRITICAL"]),
                    "points": expired_doc_pts,
                    "explanation": f"{len([e for e in expiry_findings if e['severity'] == 'CRITICAL'])} document(s) have passed their statutory validity date."
                },
                {
                    "factor": "Low-Confidence Extractions",
                    "weight_per_item": 10,
                    "item_count": len(low_confidence_extractions),
                    "points": low_conf_pts,
                    "explanation": f"{len(low_confidence_extractions)} document(s) have OCR/text extraction confidence under 70%."
                }
            ],
            "governance_rule": (
                "The Scrutiny Priority Score is an internal prioritization metric for official work queues. "
                "A low score (Standard) does NOT bypass statutory human review. "
                "A high score does NOT constitute grounds for automated rejection."
            )
        }

        # Suggested actions
        if missing_evidence:
            suggested_actions.append(f"Issue clarification letter requesting missing mandatory documents: {[m['document_type'] for m in missing_evidence]}")
        if inconsistencies:
            suggested_actions.append("Request institutional affidavit explaining discrepancies in declared vs documented land/built-up area.")
        if any(e["severity"] == "CRITICAL" for e in expiry_findings):
            suggested_actions.append("Mandate submission of renewed Fire Safety / Occupancy certificate prior to Committee Review.")
        if not missing_evidence and not inconsistencies and not expiry_findings:
            suggested_actions.append("All primary document checks passed. Application ready for Expert Visiting Committee (EVC) scheduling.")

        # Check existing report version
        prev_report = db.query(ScrutinyReport).filter(
            ScrutinyReport.application_id == application_id
        ).order_by(ScrutinyReport.report_version.desc()).first()

        new_version = (prev_report.report_version + 1) if prev_report else 1

        report = ScrutinyReport(
            application_id=application_id,
            report_version=new_version,
            priority_score=priority_score,
            priority_band=priority_band,
            score_formula_breakdown=score_formula_breakdown,
            document_inventory=document_inventory,
            extracted_summary=extracted_summary,
            missing_evidence=missing_evidence,
            inconsistencies=inconsistencies,
            expiry_findings=expiry_findings,
            low_confidence_extractions=low_confidence_extractions,
            findings_requiring_human_review=findings_requiring_human_review,
            rules_checked=rules_checked,
            suggested_actions=suggested_actions,
            reviewer_decision="PENDING"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @classmethod
    def record_official_review(
        cls,
        db: Session,
        report_id: int,
        user: User,
        decision: str,
        notes: Optional[str] = None
    ) -> ScrutinyReport:
        report = db.query(ScrutinyReport).filter(ScrutinyReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Scrutiny report not found")

        report.reviewer_decision = decision
        report.reviewer_notes = notes
        report.reviewed_by_user_id = user.id
        report.reviewed_at = datetime.datetime.utcnow()
        report.updated_at = datetime.datetime.utcnow()

        db.commit()
        db.refresh(report)
        return report
