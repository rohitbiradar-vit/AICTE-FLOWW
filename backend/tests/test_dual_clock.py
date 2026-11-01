import pytest
import datetime
from fastapi.testclient import TestClient

def test_dual_clock_summary_calculation(client: TestClient, scrutiny_officer_token: str):
    apps = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"}
    ).json()
    assert len(apps) > 0
    app_id = apps[0]["id"]

    res = client.get(
        f"/api/v1/applications/{app_id}/clock-summary",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"}
    )
    assert res.status_code == 200
    data = res.json()

    assert "institution_clock" in data
    assert "official_clock" in data
    assert "total_elapsed" in data
    assert "interval_breakdown" in data
    assert "rule_version" in data
    assert "explanation" in data

    # Check clock numbers are non-negative
    assert data["institution_clock"]["total_seconds"] >= 0.0
    assert data["official_clock"]["total_seconds"] >= 0.0

def test_clock_pause_and_resume(client: TestClient, admin_token: str):
    apps = client.get(
        "/api/v1/applications?status=IN_PROGRESS",
        headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert len(apps) > 0
    app_id = apps[0]["id"]

    # Pause clock
    pause_res = client.post(
        f"/api/v1/applications/{app_id}/clock/pause",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "reason": "Authorized pause: Public hearing inquiry",
            "authorized_clause": "APH 2026 Cl. 4.2"
        }
    )
    assert pause_res.status_code == 200
    assert "Clock paused successfully" in pause_res.json()["message"]

    # Resume clock
    resume_res = client.post(
        f"/api/v1/applications/{app_id}/clock/resume",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resume_res.status_code == 200
    assert "Clock resumed successfully" in resume_res.json()["message"]
