import os
import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.evc import EVCVisit, EVCStatus
from app.models.compliance import Undertaking, UndertakingStatus
from app.models.document import Document
from app.models.application import Application
from app.models.user import User

@pytest.fixture
def test_files(db_session: Session):
    """Creates temporary test files in storage directory and cleans them up after tests."""
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    report_filename = f"test_evc_report_{uuid.uuid4().hex[:6]}.pdf"
    report_path = os.path.join(settings.STORAGE_DIR, report_filename)
    with open(report_path, "wb") as f:
        f.write(b"%PDF-1.4 simulated EVC inspection report content for testing")

    evidence_filename = f"test_compliance_evidence_{uuid.uuid4().hex[:6]}.pdf"
    evidence_path = os.path.join(settings.STORAGE_DIR, evidence_filename)
    with open(evidence_path, "wb") as f:
        f.write(b"%PDF-1.4 simulated compliance evidence content for testing")

    yield {
        "report_filename": report_filename,
        "report_path": report_path,
        "evidence_filename": evidence_filename,
        "evidence_path": evidence_path,
    }

    # Cleanup
    if os.path.exists(report_path):
        os.remove(report_path)
    if os.path.exists(evidence_path):
        os.remove(evidence_path)

def test_unauthenticated_downloads(client: TestClient):
    # Unauthenticated EVC report download -> 401
    res1 = client.get("/api/v1/evc/1/download-report")
    assert res1.status_code == 401

    # Unauthenticated compliance evidence download -> 401
    res2 = client.get("/api/v1/compliance/undertakings/1/download-evidence")
    assert res2.status_code == 401

def test_invalid_ids_return_404(client: TestClient, admin_token: str):
    # Invalid EVC visit ID -> 404
    res1 = client.get(
        "/api/v1/evc/999999/download-report",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res1.status_code == 404
    assert "EVC visit not found" in res1.json()["detail"]

    # Invalid Undertaking ID -> 404
    res2 = client.get(
        "/api/v1/compliance/undertakings/999999/download-evidence",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res2.status_code == 404
    assert "Undertaking not found" in res2.json()["detail"]

def test_evc_report_download_success_and_missing_file(
    client: TestClient,
    db_session: Session,
    institution_token: str,
    admin_token: str,
    test_files: dict
):
    user = db_session.query(User).filter(User.email == "institution@flowguard.aicte.gov.in").first()
    app = db_session.query(Application).filter(Application.institution_id == user.institution_id).first()

    # 1. Create a visit with report attached
    visit = EVCVisit(
        visit_reference=f"EVC-TEST-{uuid.uuid4().hex[:6].upper()}",
        application_id=app.id,
        institution_id=user.institution_id,
        proposed_date=datetime.datetime.utcnow(),
        confirmed_date=datetime.datetime.utcnow(),
        status=EVCStatus.COMPLETED,
        visit_outcome="RECOMMENDED",
        report_filename=test_files["report_filename"],
        report_file_path=test_files["report_path"],
        report_summary="All infrastructure verified successfully."
    )
    db_session.add(visit)
    db_session.commit()
    db_session.refresh(visit)

    # Institution downloads their own EVC report
    res = client.get(
        f"/api/v1/evc/{visit.id}/download-report",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert res.status_code == 200
    assert "application/pdf" in res.headers["content-type"]
    assert b"simulated EVC inspection report" in res.content

    # Admin downloads report
    res_admin = client.get(
        f"/api/v1/evc/{visit.id}/download-report",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200
    assert b"simulated EVC inspection report" in res_admin.content

    # 2. Test when file is missing from filesystem -> 404
    visit.report_file_path = os.path.join(settings.STORAGE_DIR, "non_existent_report_file.pdf")
    db_session.commit()

    res_missing = client.get(
        f"/api/v1/evc/{visit.id}/download-report",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert res_missing.status_code == 404
    assert "Underlying report file not found in storage" in res_missing.json()["detail"]

def test_evc_report_unauthorized_institution_access(
    client: TestClient,
    db_session: Session,
    other_institution_token: str,
    test_files: dict
):
    # Visit belongs to Institution 1
    user1 = db_session.query(User).filter(User.email == "institution@flowguard.aicte.gov.in").first()
    app = db_session.query(Application).filter(Application.institution_id == user1.institution_id).first()

    visit = EVCVisit(
        visit_reference=f"EVC-ISO-{uuid.uuid4().hex[:6].upper()}",
        application_id=app.id,
        institution_id=user1.institution_id,
        proposed_date=datetime.datetime.utcnow(),
        status=EVCStatus.COMPLETED,
        report_filename=test_files["report_filename"],
        report_file_path=test_files["report_path"]
    )
    db_session.add(visit)
    db_session.commit()
    db_session.refresh(visit)

    # Institution 2 (other_institution_token) attempts to access Institution 1's report -> 403
    res = client.get(
        f"/api/v1/evc/{visit.id}/download-report",
        headers={"Authorization": f"Bearer {other_institution_token}"}
    )
    assert res.status_code == 403
    assert "Unauthorized" in res.json()["detail"]

def test_evc_report_download_path_traversal_protection(
    client: TestClient,
    db_session: Session,
    institution_token: str
):
    user = db_session.query(User).filter(User.email == "institution@flowguard.aicte.gov.in").first()
    app = db_session.query(Application).filter(Application.institution_id == user.institution_id).first()

    # Create visit with malicious traversal path outside STORAGE_DIR
    traversal_path = os.path.abspath(os.path.join(settings.STORAGE_DIR, "..", "..", "evil.txt"))
    visit = EVCVisit(
        visit_reference=f"EVC-TRAV-{uuid.uuid4().hex[:6].upper()}",
        application_id=app.id,
        institution_id=user.institution_id,
        proposed_date=datetime.datetime.utcnow(),
        status=EVCStatus.COMPLETED,
        report_filename="evil.txt",
        report_file_path=traversal_path
    )
    db_session.add(visit)
    db_session.commit()
    db_session.refresh(visit)

    res = client.get(
        f"/api/v1/evc/{visit.id}/download-report",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert res.status_code == 403
    assert "Access denied: invalid file path" in res.json()["detail"]

def test_compliance_evidence_download_success_and_missing(
    client: TestClient,
    db_session: Session,
    institution_token: str,
    admin_token: str,
    test_files: dict
):
    user = db_session.query(User).filter(User.email == "institution@flowguard.aicte.gov.in").first()

    # Create undertaking with evidence
    ut = Undertaking(
        undertaking_code=f"UT-TEST-{uuid.uuid4().hex[:6].upper()}",
        institution_id=user.institution_id,
        title="Fire Safety Certificate Undertaking",
        requirement_clause="AICTE APH 2026 Cl. 4.2",
        description="Provide updated fire NOC",
        due_date=datetime.datetime.utcnow() + datetime.timedelta(days=30),
        status=UndertakingStatus.SUBMITTED,
        evidence_filename=test_files["evidence_filename"],
        evidence_file_path=test_files["evidence_path"],
        submission_version=1
    )
    db_session.add(ut)
    db_session.commit()
    db_session.refresh(ut)

    # Institution downloads their own evidence
    res = client.get(
        f"/api/v1/compliance/undertakings/{ut.id}/download-evidence",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert res.status_code == 200
    assert "application/pdf" in res.headers["content-type"]
    assert b"simulated compliance evidence" in res.content

    # Admin downloads evidence
    res_admin = client.get(
        f"/api/v1/compliance/undertakings/{ut.id}/download-evidence",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200
    assert b"simulated compliance evidence" in res_admin.content

    # Missing file on disk -> 404
    ut.evidence_file_path = os.path.join(settings.STORAGE_DIR, "missing_evidence_file.pdf")
    db_session.commit()

    res_missing = client.get(
        f"/api/v1/compliance/undertakings/{ut.id}/download-evidence",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert res_missing.status_code == 404
    assert "Underlying evidence file not found in storage" in res_missing.json()["detail"]

def test_compliance_evidence_unauthorized_institution_access(
    client: TestClient,
    db_session: Session,
    other_institution_token: str,
    test_files: dict
):
    user1 = db_session.query(User).filter(User.email == "institution@flowguard.aicte.gov.in").first()

    ut = Undertaking(
        undertaking_code=f"UT-ISO-{uuid.uuid4().hex[:6].upper()}",
        institution_id=user1.institution_id,
        title="Barrier Free Ramp Undertaking",
        requirement_clause="AICTE APH 2026 Cl. 5.1",
        description="Submit geo-tagged photos of ramp",
        due_date=datetime.datetime.utcnow() + datetime.timedelta(days=20),
        status=UndertakingStatus.SUBMITTED,
        evidence_filename=test_files["evidence_filename"],
        evidence_file_path=test_files["evidence_path"]
    )
    db_session.add(ut)
    db_session.commit()
    db_session.refresh(ut)

    # Institution 2 attempts to download Institution 1's evidence -> 403
    res = client.get(
        f"/api/v1/compliance/undertakings/{ut.id}/download-evidence",
        headers={"Authorization": f"Bearer {other_institution_token}"}
    )
    assert res.status_code == 403
    assert "Unauthorized" in res.json()["detail"]

def test_compliance_evidence_path_traversal_protection(
    client: TestClient,
    db_session: Session,
    institution_token: str
):
    user = db_session.query(User).filter(User.email == "institution@flowguard.aicte.gov.in").first()

    traversal_path = os.path.abspath(os.path.join(settings.STORAGE_DIR, "..", "..", "passwords.txt"))
    ut = Undertaking(
        undertaking_code=f"UT-TRAV-{uuid.uuid4().hex[:6].upper()}",
        institution_id=user.institution_id,
        title="Path Traversal Test Undertaking",
        requirement_clause="AICTE APH 2026 Cl. 1.1",
        description="Test path traversal defense",
        due_date=datetime.datetime.utcnow() + datetime.timedelta(days=10),
        status=UndertakingStatus.SUBMITTED,
        evidence_filename="passwords.txt",
        evidence_file_path=traversal_path
    )
    db_session.add(ut)
    db_session.commit()
    db_session.refresh(ut)

    res = client.get(
        f"/api/v1/compliance/undertakings/{ut.id}/download-evidence",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert res.status_code == 403
    assert "Access denied: invalid file path" in res.json()["detail"]

def test_document_download_path_traversal_protection(
    client: TestClient,
    db_session: Session,
    institution_token: str
):
    user = db_session.query(User).filter(User.email == "institution@flowguard.aicte.gov.in").first()

    traversal_path = os.path.abspath(os.path.join(settings.STORAGE_DIR, "..", "..", "system_secret.txt"))
    doc = Document(
        document_uuid=str(uuid.uuid4()),
        storage_filename="system_secret.txt",
        document_type="OTHER",
        title="Path Traversal Test Document",
        original_filename="secret.txt",
        file_path=traversal_path,
        file_size_bytes=100,
        mime_type="text/plain",
        sha256_hash="dummyhash",
        institution_id=user.institution_id,
        version=1,
        is_current=True
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    res = client.get(
        f"/api/v1/documents/{doc.id}/download",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert res.status_code == 403
    assert "Access denied: invalid file path" in res.json()["detail"]

