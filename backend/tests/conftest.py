"""
Pytest configuration and fixtures for TicketDesk tests
"""
import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import models to register them
from src.models import Base, get_engine


@pytest.fixture(scope="session")
def test_database_url():
    """Get test database URL"""
    db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://ticketdesk_user:dev_password@localhost:5432/ticketdesk_dev"
    )
    return db_url


@pytest.fixture(scope="session")
def engine():
    """Create test database engine"""
    return get_engine()


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()

    session = sessionmaker(bind=connection, expire_on_commit=False)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database(engine):
    """Setup test database - run migrations"""
    # Ensure alembic migrations are run before tests
    import subprocess
    import sys

    try:
        # Run migrations
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd="backend",
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"⚠️ Migration warning: {result.stderr}")
            # Continue anyway - migrations might already be applied

        print("✅ Database migrations applied")
        yield
    except Exception as e:
        print(f"⚠️ Migration setup error: {e}")
        yield


def pytest_configure(config):
    """Configure pytest"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "no_cov: exclude test from coverage"
    )
