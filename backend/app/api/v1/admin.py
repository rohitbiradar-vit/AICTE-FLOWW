from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles, hash_password
from app.models.user import User, RoleEnum
from app.models.institution import Institution
from app.models.workflow import WorkflowDefinition, WorkflowStage, WorkflowTransition, DeadlineRule, HolidayRule
from app.models.audit import AuditEvent
from app.schemas.auth import UserResponse, UserCreate
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/admin", tags=["System Administration"])

# --- User Management ---
@router.get("/users", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = None,
    current_user: User = Depends(require_roles([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.id.asc()).all()

@router.post("/users", response_model=UserResponse)
def create_user(
    req: UserCreate,
    current_user: User = Depends(require_roles([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
        designation=req.designation,
        region=req.region,
        institution_id=req.institution_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="ADMIN_CREATE_USER",
        entity_type="USER",
        entity_id=user.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"created_email": req.email, "role": req.role}
    )
    db.commit()

    return user

# --- Institution Management ---
@router.get("/institutions")
def list_institutions(
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.BUREAU_AUTHORITY, RoleEnum.REGIONAL_OFFICER])),
    db: Session = Depends(get_db)
):
    insts = db.query(Institution).order_by(Institution.name.asc()).all()
    return [
        {
            "id": i.id,
            "aicte_id": i.aicte_id,
            "name": i.name,
            "institute_type": i.institute_type,
            "region": i.region,
            "state": i.state,
            "contact_email": i.contact_email,
            "status": i.status,
            "created_at": i.created_at.isoformat()
        }
        for i in insts
    ]

# --- Workflow Configurations ---
@router.get("/workflow/definitions")
def get_workflow_definitions(
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.BUREAU_AUTHORITY])),
    db: Session = Depends(get_db)
):
    wfs = db.query(WorkflowDefinition).all()
    res = []
    for wf in wfs:
        res.append({
            "id": wf.id,
            "code": wf.code,
            "name": wf.name,
            "version": wf.version,
            "is_active": wf.is_active,
            "stages": [
                {
                    "stage_key": s.stage_key,
                    "stage_name": s.stage_name,
                    "stage_order": s.stage_order,
                    "sla_hours": s.sla_hours,
                    "clock_attribution": s.clock_attribution,
                    "allowed_roles": s.allowed_roles,
                    "is_terminal": s.is_terminal
                }
                for s in wf.stages
            ],
            "transitions": [
                {
                    "id": t.id,
                    "from_stage_key": t.from_stage_key,
                    "to_stage_key": t.to_stage_key,
                    "transition_name": t.transition_name,
                    "allowed_roles": t.allowed_roles,
                    "requires_reason": t.requires_reason,
                    "prerequisites": t.prerequisites
                }
                for t in wf.transitions
            ]
        })
    return res

@router.put("/workflow/transitions/{transition_id}")
def update_workflow_transition(
    transition_id: int,
    allowed_roles: Optional[List[str]] = None,
    requires_reason: Optional[bool] = None,
    prerequisites: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(require_roles([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    trans = db.query(WorkflowTransition).filter(WorkflowTransition.id == transition_id).first()
    if not trans:
        raise HTTPException(status_code=404, detail="Workflow transition not found")

    if allowed_roles is not None:
        trans.allowed_roles = allowed_roles
    if requires_reason is not None:
        trans.requires_reason = requires_reason
    if prerequisites is not None:
        trans.prerequisites = prerequisites

    db.commit()
    return {"message": "Transition updated successfully", "id": transition_id}

# --- Audit Logs ---
@router.get("/audit-logs")
def get_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.BUREAU_AUTHORITY])),
    db: Session = Depends(get_db)
):
    query = db.query(AuditEvent)
    if action:
        query = query.filter(AuditEvent.action == action)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)

    total = query.count()
    events = query.order_by(AuditEvent.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "events": [
            {
                "id": e.id,
                "user_id": e.user_id,
                "user_email": e.user_email or "System",
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "ip_address": e.ip_address,
                "details": e.details,
                "created_at": e.created_at.isoformat()
            }
            for e in events
        ]
    }
