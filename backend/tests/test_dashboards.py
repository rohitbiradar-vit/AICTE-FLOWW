import pytest
from fastapi.testclient import TestClient

def test_institution_dashboard(client: TestClient, institution_token: str):
    res = client.get(
        "/api/v1/dashboards/institution",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "stage_distribution" in data
    assert data["metrics"]["total_applications"] > 0

def test_official_dashboard(client: TestClient, scrutiny_officer_token: str):
    res = client.get(
        "/api/v1/dashboards/official",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "work_queue_count" in data
    assert "stage_breakdown" in data
    assert "clock_averages" in data
    assert "bottlenecks" in data

def test_admin_dashboard_and_csv_export(client: TestClient, admin_token: str):
    res = client.get(
        "/api/v1/dashboards/admin",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "system_metrics" in data
    assert "regional_distribution" in data

    # CSV Export
    csv_res = client.get(
        "/api/v1/dashboards/export/applications-csv",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")
    assert "Application Number,Institution Name" in csv_res.text
