import os
os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
os.environ['JWT_ALGORITHM'] = 'HS256'
os.environ['CORS_ORIGINS'] = 'http://localhost:8000'
os.environ['HTTP_ONLY'] = 'False'
os.environ['SECURE'] = 'False'
os.environ['GROQ_API_KEY'] = 'test-groq-api-key'

import sys
from unittest.mock import MagicMock
from datetime import datetime

mock_crab_instance = MagicMock()
mock_crab_instance.predict_next_days.return_value = [
    [datetime(2026, 1, 1, 0, 0, 0), 10.0, 400.0],
    [datetime(2026, 1, 2, 0, 0, 0), 10.5, 410.0],
    [datetime(2026, 1, 3, 0, 0, 0), 11.0, 420.0],
    [datetime(2026, 1, 4, 0, 0, 0), 11.5, 430.0],
    [datetime(2026, 1, 5, 0, 0, 0), 12.0, 440.0],
    [datetime(2026, 1, 6, 0, 0, 0), 12.5, 450.0],
    [datetime(2026, 1, 7, 0, 0, 0), 13.0, 460.0],
]

mock_ai_instance = MagicMock()
mock_ai_instance.chat_from_db.return_value = ("Mock AI response", "knowledge")

crab_pred_mod = MagicMock()
crab_pred_mod.CrabPrediction = MagicMock(return_value=mock_crab_instance)
sys.modules['services.crab_prediction'] = crab_pred_mod

sched_mod = MagicMock()
sched_mod.SchedulerManager = MagicMock(return_value=MagicMock())
sys.modules['services.scheduler_manager'] = sched_mod

agents_mod = MagicMock()
agents_mod.AiAssistant = MagicMock(return_value=mock_ai_instance)
sys.modules['services.agents'] = agents_mod
sys.modules['services.agents.prompts'] = MagicMock()

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import tempfile, os

_test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db_path = _test_db.name
_test_db.close()

from database import database
test_engine = create_engine(f"sqlite:///{_test_db_path}", echo=False, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

database.engine = test_engine
database.SessionLocal = TestSessionLocal

import models
from database import Base as DatabaseBase
DatabaseBase.metadata.create_all(bind=test_engine)
DatabaseBase.metadata.create_all = lambda *a, **kw: None

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    test_engine.dispose()
    if os.path.exists(_test_db_path):
        os.unlink(_test_db_path)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    for table in reversed(list(DatabaseBase.metadata.sorted_tables)):
        with test_engine.connect() as conn:
            conn.execute(table.delete())
            conn.commit()

@pytest.fixture
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def app():
    from App import app as _app
    from routers.auth import get_db as auth_get_db
    from routers.crabs import get_db as crabs_get_db
    from routers.settings import get_db as settings_get_db
    from routers.prediction import get_db as prediction_get_db
    from routers.activity_logs import get_db as logs_get_db
    from routers.chat import get_db as chat_get_db

    def _override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    _app.dependency_overrides[auth_get_db] = _override_get_db
    _app.dependency_overrides[crabs_get_db] = _override_get_db
    _app.dependency_overrides[settings_get_db] = _override_get_db
    _app.dependency_overrides[prediction_get_db] = _override_get_db
    _app.dependency_overrides[logs_get_db] = _override_get_db
    _app.dependency_overrides[chat_get_db] = _override_get_db
    return _app


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture
def access_token():
    from services import JWTManager
    jwt = JWTManager()
    return jwt.create_access_token({
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "role": "admin"
    })


@pytest.fixture
def refresh_token():
    from services import JWTManager
    jwt = JWTManager()
    return jwt.create_refresh_token({
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "role": "admin"
    })
