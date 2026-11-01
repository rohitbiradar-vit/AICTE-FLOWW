import pytest
import datetime
from fastapi.testclient import TestClient

def test_evc_scheduling_and_conflict_check(client: TestClient, admin_token: str):
    import uuid
    apps = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    app_id = apps[0]["id"]

    visit_date = (datetime.datetime.utcnow() + datetime.timedelta(days=25)).isoformat()
    unique_email = f"officer_{uuid.uuid4().hex[:6]}@aicte.gov.in"

    # Schedule visit 1
    res1 = client.post(
        "/api/v1/evc/schedule",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_id": app_id,
            "proposed_date": visit_date,
            "assigned_officers": [
                {"name": "Dr. Conflict Test", "email": unique_email}
            ]
        }
    )
    assert res1.status_code == 200

    # Try scheduling visit 2 on same date with SAME officer -> Should fail with 409 Conflict!
    res2 = client.post(
        "/api/v1/evc/schedule",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_id": apps[1]["id"],
            "proposed_date": visit_date,
            "assigned_officers": [
                {"name": "Dr. Conflict Test", "email": unique_email}
            ]
        }
    )
    assert res2.status_code == 409
    assert "Scheduling Conflict" in res2.json()["detail"]

def test_compliance_undertakings_and_expiry_register(client: TestClient, admin_token: str):
    res = client.get(
        "/api/v1/compliance/undertakings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    uts = res.json()
    assert len(uts) > 0

    # Expiry register
    exp_res = client.get(
        "/api/v1/compliance/document-expiry-register",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert exp_res.status_code == 200
    exp_docs = exp_res.json()
    assert len(exp_docs) > 0
    assert "expiry_status" in exp_docs[0]
