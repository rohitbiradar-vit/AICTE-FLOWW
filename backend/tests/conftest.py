import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.user import User, RoleEnum

@pytest.fixture(scope="session")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def institution_token(db_session: Session):
    user = db_session.query(User).filter(User.email == "institution@flowguard.aicte.gov.in").first()
    return create_access_token(data={"sub": str(user.id), "role": user.role})

@pytest.fixture
def other_institution_token(db_session: Session):
    user = db_session.query(User).filter(User.email == "saraswati@flowguard.aicte.gov.in").first()
    return create_access_token(data={"sub": str(user.id), "role": user.role})

@pytest.fixture
def scrutiny_officer_token(db_session: Session):
    user = db_session.query(User).filter(User.email == "scrutiny.officer@aicte.gov.in").first()
    return create_access_token(data={"sub": str(user.id), "role": user.role})

@pytest.fixture
def admin_token(db_session: Session):
    user = db_session.query(User).filter(User.email == "admin@flowguard.aicte.gov.in").first()
    return create_access_token(data={"sub": str(user.id), "role": user.role})
