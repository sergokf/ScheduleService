import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.database import get_async_session
from app.models.base import BaseModel

# Тестовая база данных
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.create_all)

        async with AsyncSession(bind=connection) as session:
            yield session

        await connection.run_sync(BaseModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database session override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def teacher_data():
    unique_email = f"teacher_{uuid.uuid4()}@test.com"
    return {
        "name": "Test Teacher",
        "email": unique_email,
        "phone": "+1234567890",
        "bio": "Test teacher bio"
    }

@pytest.fixture
def student_data():
    unique_email = f"student_{uuid.uuid4()}@test.com"
    return {
        "name": "Test Student",
        "email": unique_email,
        "phone": "+1234567890"
    }

@pytest.fixture
def slot_data(teacher_data):
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    return {
        "teacher_id": 1,  # будет заменено после создания учителя
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=1)).isoformat(),
        "max_students": 1,
        "description": "Test slot"
    }

@pytest.fixture
async def test_teacher(client: AsyncClient, teacher_data):
    response = await client.post("/api/v1/teachers/", json=teacher_data)
    assert response.status_code == 200, f"Failed to create teacher: {response.text}"
    return response.json()

@pytest.fixture
async def test_student(client: AsyncClient, student_data):
    response = await client.post("/api/v1/students/", json=student_data)
    assert response.status_code == 200, f"Failed to create student: {response.text}"
    return response.json()

@pytest.fixture
async def test_time_slot(client: AsyncClient, test_teacher, slot_data):
    slot_data = dict(slot_data)
    slot_data["teacher_id"] = test_teacher["id"]
    response = await client.post("/api/v1/slots/", json=slot_data)
    assert response.status_code == 200, f"Failed to create slot: {response.text}"
    return response.json()
