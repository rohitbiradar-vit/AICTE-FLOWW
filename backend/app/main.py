from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.migration import run_db_migrations
from app.core.scheduler import start_scheduler, stop_scheduler
from app.api.v1 import (
    auth, applications, documents, scrutiny, evc, compliance, notifications, dashboards, admin
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database schema is migrated to Alembic head
    try:
        run_db_migrations()
    except Exception as e:
        print(f"Warning: Could not run database migrations on startup: {e}")

    # Startup: Start APScheduler
    try:
        start_scheduler()
    except Exception as e:
        print(f"Warning: Could not start scheduler: {e}")
    yield
    # Shutdown: Stop APScheduler
    try:
        stop_scheduler()
    except Exception:
        pass

app = FastAPI(
    title="AICTE - FLOWW API",
    description="Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Alert Management System (SIH Problem Statement 26262)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(applications.router, prefix=api_v1_prefix)
app.include_router(documents.router, prefix=api_v1_prefix)
app.include_router(scrutiny.router, prefix=api_v1_prefix)
app.include_router(evc.router, prefix=api_v1_prefix)
app.include_router(compliance.router, prefix=api_v1_prefix)
app.include_router(notifications.router, prefix=api_v1_prefix)
app.include_router(dashboards.router, prefix=api_v1_prefix)
app.include_router(admin.router, prefix=api_v1_prefix)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AICTE - FLOWW Backend API",
        "version": "1.0.0",
        "rule_version": settings.RULE_VERSION
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to AICTE - FLOWW API",
        "documentation": "/docs",
        "health": "/health",
        "api_v1": api_v1_prefix
    }
