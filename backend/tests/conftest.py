"""
Pytest configuration and fixtures for TicketDesk tests
"""
import pytest
import os
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import models to register them
from src.models import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine (SQLite in memory for CI/local testing)"""
    # Use SQLite in memory for testing (no external dependencies)
    # Session-scoped to persist database across all tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
        isolation_level="SERIALIZABLE"
    )

    # Enable foreign keys in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables from models
    # For now, we'll use raw SQL since we're testing migrations
    with engine.begin() as conn:
        # Create roles table
        conn.execute(text("""
            CREATE TABLE roles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                permissions TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create users table
        conn.execute(text("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role_id TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles(id)
            )
        """))

        # Create sessions table
        conn.execute(text("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                candidate_email TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                session_data TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))

        # Create audit_logs table
        conn.execute(text("""
            CREATE TABLE audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                changes TEXT DEFAULT '{}',
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))

        # Create indexes
        conn.execute(text("CREATE INDEX users_email_idx ON users(email)"))
        conn.execute(text("CREATE INDEX sessions_account_id_idx ON sessions(account_id)"))
        conn.execute(text("CREATE INDEX sessions_status_idx ON sessions(status)"))
        conn.execute(text("CREATE INDEX sessions_deleted_at_idx ON sessions(deleted_at)"))
        conn.execute(text("CREATE INDEX users_deleted_at_idx ON users(deleted_at)"))
        conn.execute(text("CREATE INDEX audit_logs_user_id_idx ON audit_logs(user_id)"))
        conn.execute(text("CREATE INDEX audit_logs_resource_idx ON audit_logs(resource, resource_id)"))
        conn.execute(text("CREATE INDEX audit_logs_created_at_idx ON audit_logs(created_at)"))

    yield engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a new database session for each test"""
    SessionLocal = sessionmaker(bind=test_engine, expire_on_commit=False)
    session = SessionLocal()

    yield session

    # Clear the session but don't rollback - persist data across tests
    session.expunge_all()
    session.close()


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
