import os
import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata

from app.core.database import Base, engine
from app.core.migration import get_alembic_config, run_db_migrations
from app.models.document import DocumentValidationFinding
import app.models  # Ensure all models are registered on Base.metadata

def test_alembic_script_directory_and_head_revision():
    """Verifies that Alembic discovers the initial schema migration script."""
    cfg = get_alembic_config()
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "001_initial"

def test_all_twenty_tables_exist_in_database():
    """Verifies that all 20 required application tables exist in the database."""
    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())

    expected_tables = {
        "holiday_rules",
        "institutions",
        "workflow_definitions",
        "deadline_rules",
        "users",
        "workflow_stages",
        "workflow_transitions",
        "applications",
        "audit_events",
        "clock_intervals",
        "documents",
        "evc_visits",
        "notifications",
        "scrutiny_reports",
        "stage_history",
        "undertakings",
        "clock_pause_logs",
        "document_extractions",
        "document_validation_findings",
        "notification_delivery_attempts",
    }

    assert "alembic_version" in db_tables, "alembic_version table is missing"
    missing_tables = expected_tables - db_tables
    assert not missing_tables, f"Missing tables in database: {missing_tables}"

def test_document_validation_finding_schema_and_columns():
    """Verifies that DocumentValidationFinding table is properly created with all columns."""
    inspector = inspect(engine)
    columns = {c["name"]: c for c in inspector.get_columns("document_validation_findings")}

    expected_columns = [
        "id", "document_id", "finding_type", "severity", "field_name",
        "declared_value", "extracted_value", "description", "citation_page",
        "is_resolved", "resolution_notes", "created_at"
    ]
    for col in expected_columns:
        assert col in columns, f"Column '{col}' missing from document_validation_findings"

    fks = inspector.get_foreign_keys("document_validation_findings")
    assert any(fk["referred_table"] == "documents" for fk in fks), "Missing FK to documents table"

def test_idempotent_migration_execution():
    """Verifies that run_db_migrations() runs idempotently on an existing database without error."""
    # Running migrations again against an up-to-date database should succeed cleanly
    run_db_migrations()

    cfg = get_alembic_config()
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        current_rev = ctx.get_current_revision()
        assert current_rev == "001_initial"

def test_zero_schema_drift():
    """Verifies that Alembic autogenerate detects zero drift between Base.metadata and database."""
    with engine.connect() as conn:
        mc = MigrationContext.configure(conn)
        diff = compare_metadata(mc, Base.metadata)
        assert len(diff) == 0, f"Schema drift detected: {diff}"
