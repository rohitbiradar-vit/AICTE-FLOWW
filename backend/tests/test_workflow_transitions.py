import pytest
from fastapi.testclient import TestClient

def test_invalid_workflow_transition_rejected(client: TestClient, scrutiny_officer_token: str):
    # Try invalid jump: Directly from DRAFT to FINAL_APPROVAL
    # Fetch an application
    apps = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"}
    ).json()
    assert len(apps) > 0
    app_id = apps[0]["id"]

    # Attempt illegal transition
    res = client.post(
        f"/api/v1/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"},
        json={
            "target_stage_key": "FINAL_APPROVAL",
            "reason": "Bypassing scrutiny"
        }
    )
    # Backend must reject invalid transitions!
    assert res.status_code in [400, 403]
    assert "Invalid transition" in res.json()["detail"] or "not permitted" in res.json()["detail"]

def test_clarification_requires_mandatory_reason(client: TestClient, scrutiny_officer_token: str):
    # Find an app in INITIAL_SCRUTINY
    apps = client.get(
        "/api/v1/applications?stage=INITIAL_SCRUTINY",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"}
    ).json()
    if not apps:
        pytest.skip("No app in INITIAL_SCRUTINY")

    app_id = apps[0]["id"]

    # Try transitioning to CLARIFICATION_REQUIRED without reason
    res = client.post(
        f"/api/v1/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"},
        json={
            "target_stage_key": "CLARIFICATION_REQUIRED",
            "reason": "" # Empty reason!
        }
    )
    assert res.status_code == 400
    assert "mandatory" in res.json()["detail"].lower()
