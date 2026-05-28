"""
User Aggregate - Domain-Driven Design

Bounded Context: Unit 1 (Account Management)
Represents the core user entity with password hashing and role-based access.

LGPD Compliance:
- Soft-delete pattern (deleted_at timestamp)
- Password hashing with bcrypt (12 rounds minimum)
- Immutable email (once set, cannot change)
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
import bcrypt

from . import Base


class Role(Base):
    """Role entity - defines user roles and permissions"""
    __tablename__ = "roles"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    permissions = Column(String, nullable=False, default="[]")  # JSON array
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class User(Base):
    """
    User Aggregate - Core user entity

    Invariants:
    - Email is unique and immutable
    - Password is hashed with bcrypt (rounds >= 12)
    - Role must exist in roles table
    - created_at and updated_at are automatically set
    - deleted_at is only set during soft-delete (LGPD compliance)
    """
    __tablename__ = "users"

    # Identity
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)

    # Access Control
    role_id = Column(PostgresUUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # LGPD soft-delete

    # Relationships
    role = relationship("Role", back_populates="users")
    sessions = relationship("Session", back_populates="account", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role_id={self.role_id})>"

    # === DOMAIN METHODS ===

    def set_password(self, password: str) -> None:
        """
        Hash and set the user's password.

        Uses bcrypt with 12 rounds for secure password hashing.
        Hashing is deterministic per password, so same password produces same hash.

        Args:
            password: Plain text password

        Raises:
            ValueError: If password is empty or None
        """
        if not password:
            raise ValueError("Password cannot be empty")

        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str) -> bool:
        """
        Verify that the provided password matches the stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        if not password or not self.password_hash:
            return False

        try:
            return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))
        except Exception:
            return False

    def soft_delete(self) -> None:
        """
        Soft-delete the user (LGPD compliance).

        Sets deleted_at to current time. User is logically deleted but data is retained.
        Hard delete should occur 24 hours later via worker process.

        Invariant: deleted_at can only be set once
        """
        if self.deleted_at is not None:
            raise ValueError("User is already deleted")

        self.deleted_at = datetime.utcnow()
        self.is_active = False

    def restore(self) -> None:
        """
        Restore a soft-deleted user (before hard-delete window).

        Only works if user was soft-deleted recently.
        """
        if self.deleted_at is None:
            raise ValueError("User is not deleted")

        self.deleted_at = None
        self.is_active = True

    def is_deleted(self) -> bool:
        """Check if user is soft-deleted"""
        return self.deleted_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if user is valid and active"""
        return self.is_active and not self.is_deleted()


# Import Session and AuditLog after User is defined to avoid circular imports
from .session import Session
from .audit_log import AuditLog

__all__ = ["User", "Role"]
