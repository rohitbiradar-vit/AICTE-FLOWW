"""Initial schema for AICTE FlowGuard

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-28 22:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. holiday_rules
    if 'holiday_rules' not in existing_tables:
        op.create_table(
            'holiday_rules',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('date', sa.DateTime(), nullable=False),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('is_recurring', sa.Boolean(), nullable=True),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_holiday_rules_date'), 'holiday_rules', ['date'], unique=True)
        op.create_index(op.f('ix_holiday_rules_id'), 'holiday_rules', ['id'], unique=False)

    # 2. institutions
    if 'institutions' not in existing_tables:
        op.create_table(
            'institutions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('aicte_id', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('institute_type', sa.String(length=100), nullable=True),
            sa.Column('region', sa.String(length=100), nullable=False),
            sa.Column('state', sa.String(length=100), nullable=False),
            sa.Column('district', sa.String(length=100), nullable=True),
            sa.Column('address', sa.Text(), nullable=False),
            sa.Column('contact_email', sa.String(length=255), nullable=False),
            sa.Column('contact_phone', sa.String(length=50), nullable=True),
            sa.Column('website', sa.String(length=255), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('metadata_info', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_institutions_aicte_id'), 'institutions', ['aicte_id'], unique=True)
        op.create_index(op.f('ix_institutions_id'), 'institutions', ['id'], unique=False)

    # 3. workflow_definitions
    if 'workflow_definitions' not in existing_tables:
        op.create_table(
            'workflow_definitions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('version', sa.String(length=50), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workflow_definitions_code'), 'workflow_definitions', ['code'], unique=True)
        op.create_index(op.f('ix_workflow_definitions_id'), 'workflow_definitions', ['id'], unique=False)

    # 4. deadline_rules
    if 'deadline_rules' not in existing_tables:
        op.create_table(
            'deadline_rules',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('stage_key', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('max_duration_hours', sa.Integer(), nullable=False),
            sa.Column('warning_threshold_hours', sa.Integer(), nullable=True),
            sa.Column('escalation_role', sa.String(length=50), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_deadline_rules_id'), 'deadline_rules', ['id'], unique=False)
        op.create_index(op.f('ix_deadline_rules_stage_key'), 'deadline_rules', ['stage_key'], unique=False)

    # 5. users
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('full_name', sa.String(length=255), nullable=False),
            sa.Column('role', sa.String(length=50), nullable=False),
            sa.Column('designation', sa.String(length=100), nullable=True),
            sa.Column('region', sa.String(length=100), nullable=True),
            sa.Column('institution_id', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
        op.create_index(op.f('ix_users_institution_id'), 'users', ['institution_id'], unique=False)
        op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 6. workflow_stages
    if 'workflow_stages' not in existing_tables:
        op.create_table(
            'workflow_stages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('stage_key', sa.String(length=50), nullable=False),
            sa.Column('stage_name', sa.String(length=100), nullable=False),
            sa.Column('stage_order', sa.Integer(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('sla_hours', sa.Integer(), nullable=True),
            sa.Column('clock_attribution', sa.String(length=50), nullable=False),
            sa.Column('allowed_roles', sa.JSON(), nullable=True),
            sa.Column('is_terminal', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workflow_stages_id'), 'workflow_stages', ['id'], unique=False)
        op.create_index(op.f('ix_workflow_stages_stage_key'), 'workflow_stages', ['stage_key'], unique=False)
        op.create_index(op.f('ix_workflow_stages_workflow_id'), 'workflow_stages', ['workflow_id'], unique=False)

    # 7. workflow_transitions
    if 'workflow_transitions' not in existing_tables:
        op.create_table(
            'workflow_transitions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('from_stage_key', sa.String(length=50), nullable=False),
            sa.Column('to_stage_key', sa.String(length=50), nullable=False),
            sa.Column('transition_name', sa.String(length=100), nullable=False),
            sa.Column('allowed_roles', sa.JSON(), nullable=True),
            sa.Column('requires_reason', sa.Boolean(), nullable=True),
            sa.Column('prerequisites', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workflow_transitions_from_stage_key'), 'workflow_transitions', ['from_stage_key'], unique=False)
        op.create_index(op.f('ix_workflow_transitions_id'), 'workflow_transitions', ['id'], unique=False)
        op.create_index(op.f('ix_workflow_transitions_to_stage_key'), 'workflow_transitions', ['to_stage_key'], unique=False)
        op.create_index(op.f('ix_workflow_transitions_workflow_id'), 'workflow_transitions', ['workflow_id'], unique=False)

    # 8. applications
    if 'applications' not in existing_tables:
        op.create_table(
            'applications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('application_number', sa.String(length=50), nullable=False),
            sa.Column('institution_id', sa.Integer(), nullable=False),
            sa.Column('academic_year', sa.String(length=20), nullable=False),
            sa.Column('application_type', sa.String(length=100), nullable=False),
            sa.Column('current_stage_key', sa.String(length=50), nullable=False),
            sa.Column('workflow_code', sa.String(length=50), nullable=True),
            sa.Column('assigned_official_id', sa.Integer(), nullable=True),
            sa.Column('declared_land_acres', sa.String(length=50), nullable=True),
            sa.Column('declared_builtup_sqm', sa.String(length=50), nullable=True),
            sa.Column('declared_intake', sa.Integer(), nullable=True),
            sa.Column('declared_faculty_count', sa.Integer(), nullable=True),
            sa.Column('application_data', sa.JSON(), nullable=True),
            sa.Column('clarification_notes', sa.Text(), nullable=True),
            sa.Column('resubmission_count', sa.Integer(), nullable=True),
            sa.Column('current_deadline', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['assigned_official_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_applications_application_number'), 'applications', ['application_number'], unique=True)
        op.create_index(op.f('ix_applications_assigned_official_id'), 'applications', ['assigned_official_id'], unique=False)
        op.create_index(op.f('ix_applications_current_stage_key'), 'applications', ['current_stage_key'], unique=False)
        op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)
        op.create_index(op.f('ix_applications_institution_id'), 'applications', ['institution_id'], unique=False)
        op.create_index(op.f('ix_applications_status'), 'applications', ['status'], unique=False)

    # 9. audit_events
    if 'audit_events' not in existing_tables:
        op.create_table(
            'audit_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('user_email', sa.String(length=255), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('ip_address', sa.String(length=50), nullable=True),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_audit_events_action'), 'audit_events', ['action'], unique=False)
        op.create_index(op.f('ix_audit_events_created_at'), 'audit_events', ['created_at'], unique=False)
        op.create_index(op.f('ix_audit_events_entity_id'), 'audit_events', ['entity_id'], unique=False)
        op.create_index(op.f('ix_audit_events_entity_type'), 'audit_events', ['entity_type'], unique=False)
        op.create_index(op.f('ix_audit_events_id'), 'audit_events', ['id'], unique=False)
        op.create_index(op.f('ix_audit_events_user_id'), 'audit_events', ['user_id'], unique=False)

    # 10. clock_intervals
    if 'clock_intervals' not in existing_tables:
        op.create_table(
            'clock_intervals',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=False),
            sa.Column('clock_type', sa.String(length=50), nullable=False),
            sa.Column('stage_key', sa.String(length=50), nullable=False),
            sa.Column('start_time', sa.DateTime(), nullable=False),
            sa.Column('end_time', sa.DateTime(), nullable=True),
            sa.Column('elapsed_seconds', sa.Float(), nullable=True),
            sa.Column('is_paused', sa.Boolean(), nullable=True),
            sa.Column('pause_reason', sa.String(length=255), nullable=True),
            sa.Column('rule_version', sa.String(length=50), nullable=True),
            sa.Column('calculation_details', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_clock_intervals_application_id'), 'clock_intervals', ['application_id'], unique=False)
        op.create_index(op.f('ix_clock_intervals_clock_type'), 'clock_intervals', ['clock_type'], unique=False)
        op.create_index(op.f('ix_clock_intervals_id'), 'clock_intervals', ['id'], unique=False)

    # 11. documents
    if 'documents' not in existing_tables:
        op.create_table(
            'documents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('document_uuid', sa.String(length=100), nullable=False),
            sa.Column('institution_id', sa.Integer(), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=True),
            sa.Column('document_type', sa.String(length=100), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('original_filename', sa.String(length=255), nullable=False),
            sa.Column('storage_filename', sa.String(length=255), nullable=False),
            sa.Column('file_path', sa.Text(), nullable=False),
            sa.Column('file_size_bytes', sa.Integer(), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=False),
            sa.Column('sha256_hash', sa.String(length=64), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('is_current', sa.Boolean(), nullable=False),
            sa.Column('issue_date', sa.DateTime(), nullable=True),
            sa.Column('expiry_date', sa.DateTime(), nullable=True),
            sa.Column('requires_renewal', sa.Boolean(), nullable=True),
            sa.Column('verification_status', sa.String(length=50), nullable=True),
            sa.Column('verification_notes', sa.Text(), nullable=True),
            sa.Column('verified_by_user_id', sa.Integer(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('uploaded_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['verified_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_documents_application_id'), 'documents', ['application_id'], unique=False)
        op.create_index(op.f('ix_documents_document_type'), 'documents', ['document_type'], unique=False)
        op.create_index(op.f('ix_documents_document_uuid'), 'documents', ['document_uuid'], unique=True)
        op.create_index(op.f('ix_documents_expiry_date'), 'documents', ['expiry_date'], unique=False)
        op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
        op.create_index(op.f('ix_documents_institution_id'), 'documents', ['institution_id'], unique=False)
        op.create_index(op.f('ix_documents_verification_status'), 'documents', ['verification_status'], unique=False)

    # 12. evc_visits
    if 'evc_visits' not in existing_tables:
        op.create_table(
            'evc_visits',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('visit_reference', sa.String(length=50), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=False),
            sa.Column('institution_id', sa.Integer(), nullable=False),
            sa.Column('proposed_date', sa.DateTime(), nullable=False),
            sa.Column('confirmed_date', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('assigned_officers', sa.JSON(), nullable=True),
            sa.Column('coordinator_user_id', sa.Integer(), nullable=True),
            sa.Column('preparation_checklist', sa.JSON(), nullable=True),
            sa.Column('infrastructure_readiness', sa.String(length=100), nullable=True),
            sa.Column('visit_outcome', sa.String(length=100), nullable=True),
            sa.Column('report_filename', sa.String(length=255), nullable=True),
            sa.Column('report_file_path', sa.Text(), nullable=True),
            sa.Column('report_summary', sa.Text(), nullable=True),
            sa.Column('deficiencies_found', sa.JSON(), nullable=True),
            sa.Column('follow_up_required', sa.Boolean(), nullable=True),
            sa.Column('follow_up_deadline', sa.DateTime(), nullable=True),
            sa.Column('conducted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['coordinator_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_evc_visits_application_id'), 'evc_visits', ['application_id'], unique=False)
        op.create_index(op.f('ix_evc_visits_id'), 'evc_visits', ['id'], unique=False)
        op.create_index(op.f('ix_evc_visits_institution_id'), 'evc_visits', ['institution_id'], unique=False)
        op.create_index(op.f('ix_evc_visits_status'), 'evc_visits', ['status'], unique=False)
        op.create_index(op.f('ix_evc_visits_visit_reference'), 'evc_visits', ['visit_reference'], unique=True)

    # 13. notifications
    if 'notifications' not in existing_tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('notification_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=50), nullable=True),
            sa.Column('related_application_id', sa.Integer(), nullable=True),
            sa.Column('related_entity_type', sa.String(length=50), nullable=True),
            sa.Column('related_entity_id', sa.Integer(), nullable=True),
            sa.Column('action_link', sa.String(length=255), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=False),
            sa.Column('is_escalated', sa.Boolean(), nullable=False),
            sa.Column('due_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['related_application_id'], ['applications.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
        op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
        op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
        op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'], unique=False)
        op.create_index(op.f('ix_notifications_related_application_id'), 'notifications', ['related_application_id'], unique=False)
        op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # 14. scrutiny_reports
    if 'scrutiny_reports' not in existing_tables:
        op.create_table(
            'scrutiny_reports',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=False),
            sa.Column('report_version', sa.Integer(), nullable=False),
            sa.Column('priority_score', sa.Integer(), nullable=False),
            sa.Column('priority_band', sa.String(length=50), nullable=False),
            sa.Column('score_formula_breakdown', sa.JSON(), nullable=False),
            sa.Column('document_inventory', sa.JSON(), nullable=True),
            sa.Column('extracted_summary', sa.JSON(), nullable=True),
            sa.Column('missing_evidence', sa.JSON(), nullable=True),
            sa.Column('inconsistencies', sa.JSON(), nullable=True),
            sa.Column('expiry_findings', sa.JSON(), nullable=True),
            sa.Column('low_confidence_extractions', sa.JSON(), nullable=True),
            sa.Column('findings_requiring_human_review', sa.JSON(), nullable=True),
            sa.Column('rules_checked', sa.JSON(), nullable=True),
            sa.Column('suggested_actions', sa.JSON(), nullable=True),
            sa.Column('reviewer_decision', sa.String(length=50), nullable=True),
            sa.Column('reviewer_notes', sa.Text(), nullable=True),
            sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_scrutiny_reports_application_id'), 'scrutiny_reports', ['application_id'], unique=False)
        op.create_index(op.f('ix_scrutiny_reports_id'), 'scrutiny_reports', ['id'], unique=False)

    # 15. stage_history
    if 'stage_history' not in existing_tables:
        op.create_table(
            'stage_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=False),
            sa.Column('from_stage', sa.String(length=50), nullable=False),
            sa.Column('to_stage', sa.String(length=50), nullable=False),
            sa.Column('transition_name', sa.String(length=100), nullable=True),
            sa.Column('transitioned_by_user_id', sa.Integer(), nullable=True),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['transitioned_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_stage_history_application_id'), 'stage_history', ['application_id'], unique=False)
        op.create_index(op.f('ix_stage_history_created_at'), 'stage_history', ['created_at'], unique=False)
        op.create_index(op.f('ix_stage_history_id'), 'stage_history', ['id'], unique=False)

    # 16. undertakings
    if 'undertakings' not in existing_tables:
        op.create_table(
            'undertakings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('undertaking_code', sa.String(length=50), nullable=False),
            sa.Column('institution_id', sa.Integer(), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('requirement_clause', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('due_date', sa.DateTime(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('evidence_filename', sa.String(length=255), nullable=True),
            sa.Column('evidence_file_path', sa.Text(), nullable=True),
            sa.Column('evidence_description', sa.Text(), nullable=True),
            sa.Column('submission_version', sa.Integer(), nullable=True),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
            sa.Column('verified_by_user_id', sa.Integer(), nullable=True),
            sa.Column('verification_notes', sa.Text(), nullable=True),
            sa.Column('correction_reason', sa.Text(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('requires_annual_renewal', sa.Boolean(), nullable=True),
            sa.Column('renewal_due_date', sa.DateTime(), nullable=True),
            sa.Column('created_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['verified_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_undertakings_application_id'), 'undertakings', ['application_id'], unique=False)
        op.create_index(op.f('ix_undertakings_due_date'), 'undertakings', ['due_date'], unique=False)
        op.create_index(op.f('ix_undertakings_id'), 'undertakings', ['id'], unique=False)
        op.create_index(op.f('ix_undertakings_institution_id'), 'undertakings', ['institution_id'], unique=False)
        op.create_index(op.f('ix_undertakings_status'), 'undertakings', ['status'], unique=False)
        op.create_index(op.f('ix_undertakings_undertaking_code'), 'undertakings', ['undertaking_code'], unique=True)

    # 17. clock_pause_logs
    if 'clock_pause_logs' not in existing_tables:
        op.create_table(
            'clock_pause_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('interval_id', sa.Integer(), nullable=False),
            sa.Column('paused_by_user_id', sa.Integer(), nullable=True),
            sa.Column('pause_start', sa.DateTime(), nullable=False),
            sa.Column('pause_end', sa.DateTime(), nullable=True),
            sa.Column('reason', sa.Text(), nullable=False),
            sa.Column('authorized_clause', sa.String(length=100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['interval_id'], ['clock_intervals.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['paused_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_clock_pause_logs_id'), 'clock_pause_logs', ['id'], unique=False)
        op.create_index(op.f('ix_clock_pause_logs_interval_id'), 'clock_pause_logs', ['interval_id'], unique=False)

    # 18. document_extractions
    if 'document_extractions' not in existing_tables:
        op.create_table(
            'document_extractions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('document_id', sa.Integer(), nullable=False),
            sa.Column('extraction_method', sa.String(length=50), nullable=True),
            sa.Column('extracted_text_preview', sa.Text(), nullable=True),
            sa.Column('extracted_fields', sa.JSON(), nullable=True),
            sa.Column('confidence_scores', sa.JSON(), nullable=True),
            sa.Column('overall_confidence', sa.Float(), nullable=True),
            sa.Column('processing_status', sa.String(length=50), nullable=True),
            sa.Column('page_count', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_document_extractions_document_id'), 'document_extractions', ['document_id'], unique=False)
        op.create_index(op.f('ix_document_extractions_id'), 'document_extractions', ['id'], unique=False)

    # 19. document_validation_findings
    if 'document_validation_findings' not in existing_tables:
        op.create_table(
            'document_validation_findings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('document_id', sa.Integer(), nullable=False),
            sa.Column('finding_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=50), nullable=True),
            sa.Column('field_name', sa.String(length=100), nullable=True),
            sa.Column('declared_value', sa.String(length=255), nullable=True),
            sa.Column('extracted_value', sa.String(length=255), nullable=True),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('citation_page', sa.Integer(), nullable=True),
            sa.Column('is_resolved', sa.Boolean(), nullable=True),
            sa.Column('resolution_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_document_validation_findings_document_id'), 'document_validation_findings', ['document_id'], unique=False)
        op.create_index(op.f('ix_document_validation_findings_id'), 'document_validation_findings', ['id'], unique=False)

    # 20. notification_delivery_attempts
    if 'notification_delivery_attempts' not in existing_tables:
        op.create_table(
            'notification_delivery_attempts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('notification_id', sa.Integer(), nullable=False),
            sa.Column('channel', sa.String(length=50), nullable=True),
            sa.Column('attempt_time', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_notification_delivery_attempts_id'), 'notification_delivery_attempts', ['id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Drop in reverse dependency order
    tables_in_drop_order = [
        'notification_delivery_attempts',
        'document_validation_findings',
        'document_extractions',
        'clock_pause_logs',
        'undertakings',
        'stage_history',
        'scrutiny_reports',
        'notifications',
        'evc_visits',
        'documents',
        'clock_intervals',
        'audit_events',
        'applications',
        'workflow_transitions',
        'workflow_stages',
        'users',
        'deadline_rules',
        'workflow_definitions',
        'institutions',
        'holiday_rules'
    ]

    for table in tables_in_drop_order:
        if table in existing_tables:
            op.drop_table(table)
