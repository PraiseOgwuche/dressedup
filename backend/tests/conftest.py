import os
import tempfile
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("MEDIA_DIR", tempfile.mkdtemp(prefix="dressedup-test-media-"))
# Never let tests touch a real AI provider (no token spend, no network).
os.environ.setdefault("VISION_PROVIDER", "stub")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
os.environ.setdefault("NOTIFICATION_SCHEDULER_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — register all models on Base.metadata
from app.database import Base, get_db
from app.main import app


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    import app.database as db_module

    db_module.engine = engine
    db_module.SessionLocal = TestingSessionLocal
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def auth_header(client):
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    register_payload = {
        "email": email,
        "full_name": "Test User",
        "password": "password123",
    }
    client.post("/api/v1/auth/register", json=register_payload)
    login = client.post("/api/v1/auth/login", json={"email": register_payload["email"], "password": register_payload["password"]})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

