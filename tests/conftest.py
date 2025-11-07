"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Test database URL (use SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    AsyncSessionLocal = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "full_name": "Test User",
        "email": "test@neurula.health",
        "phone": "+971501234567",
        "password": "Test@1234",
        "registration_method": "manual",
        "date_of_birth": "1990-01-01",
        "gender": "Male",
        "nationality": "UAE",
        "height": 175.0,
        "weight": 70.0,
        "emirate": "Dubai",
        "city": "Dubai",
        "address": "Test Address, Dubai",
    }


@pytest.fixture
def test_login_data():
    """Sample login data for testing"""
    return {
        "username": "test@neurula.health",
        "password": "Test@1234",
        "remember_me": False,
    }
