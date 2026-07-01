from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_current_user  # noqa: F401  (import for symmetry)
from app.config import get_settings
from app.db.session import get_db
from app.main import app

settings = get_settings()
engine = create_engine(str(settings.database_url))
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Each test runs in a transaction rolled back at teardown — no data leaks."""
    connection = engine.connect()
    trans = connection.begin()
    session = TestingSession(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
