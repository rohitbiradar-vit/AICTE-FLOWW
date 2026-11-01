import pytest
from fastapi.testclient import TestClient

def test_login_success(client: TestClient):
    response = client.post("/api/v1/auth/login", json={
        "email": "institution@flowguard.aicte.gov.in",
        "password": "DemoPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "INSTITUTION"

def test_login_invalid_password(client: TestClient):
    response = client.post("/api/v1/auth/login", json={
        "email": "institution@flowguard.aicte.gov.in",
        "password": "WrongPassword999!"
    })
    assert response.status_code == 401

def test_institutional_data_isolation(client: TestClient, institution_token: str, other_institution_token: str):
    # Institution 1 lists its applications
    res1 = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert res1.status_code == 200
    apps1 = res1.json()
    assert len(apps1) > 0
    # Every app must belong to Apex (Institution 1)
    inst_ids = {a["institution_id"] for a in apps1}
    assert len(inst_ids) == 1

    # Institution 2 cannot access Institution 1's application details
    inst1_app_id = apps1[0]["id"]
    res2 = client.get(
        f"/api/v1/applications/{inst1_app_id}",
        headers={"Authorization": f"Bearer {other_institution_token}"}
    )
    assert res2.status_code == 403
    assert "Unauthorized" in res2.json()["detail"]
