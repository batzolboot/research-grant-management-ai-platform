import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# This must happen before importing app.database or app.main.
os.environ["DATABASE_URL"] = "sqlite:///./test_grants.db"

from app import auth, models  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


TEST_DATABASE_URL = "sqlite:///./test_grants.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


def override_admin_user():
    return SimpleNamespace(
        id=1,
        email="test-admin@example.com",
        role="Admin",
    )


def override_logged_in_user():
    return SimpleNamespace(
        id=1,
        email="test-admin@example.com",
        role="Admin",
    )


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[auth.require_admin] = override_admin_user
app.dependency_overrides[auth.get_current_user] = override_logged_in_user


@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client