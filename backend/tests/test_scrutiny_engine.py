import pytest
from fastapi.testclient import TestClient

def test_scrutiny_report_generation_and_scoring(client: TestClient, scrutiny_officer_token: str):
    apps = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"}
    ).json()
    app_id = apps[0]["id"]

    res = client.get(
        f"/api/v1/scrutiny/applications/{app_id}/latest",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"}
    )
    assert res.status_code == 200
    report = res.json()

    assert "priority_score" in report
    assert 0 <= report["priority_score"] <= 100
    assert report["priority_band"] in ["STANDARD", "ENHANCED", "HIGH"]
    assert "score_formula_breakdown" in report
    assert "document_inventory" in report
    assert "rules_checked" in report

def test_scrutiny_official_review_decision(client: TestClient, scrutiny_officer_token: str):
    apps = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"}
    ).json()
    app_id = apps[0]["id"]

    rep_res = client.get(
        f"/api/v1/scrutiny/applications/{app_id}/latest",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"}
    )
    report_id = rep_res.json()["id"]

    # Record official review
    review_res = client.post(
        f"/api/v1/scrutiny/reports/{report_id}/review",
        headers={"Authorization": f"Bearer {scrutiny_officer_token}"},
        json={
            "decision": "AGREED",
            "notes": "Verified extracted title deed matches sub-registrar records."
        }
    )
    assert review_res.status_code == 200
    assert review_res.json()["reviewer_decision"] == "AGREED"
