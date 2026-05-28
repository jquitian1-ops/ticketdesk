"""
UserRepository - Data Access Object for User aggregate

Implements the Repository pattern to encapsulate database access.
All user CRUD operations go through this class.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.user import User, Role


class UserRepository:
    """Repository for User aggregate"""

    def __init__(self, db_session: Session):
        """
        Initialize repository with database session

        Args:
            db_session: SQLAlchemy session
        """
        self.db = db_session

    # === CREATE ===

    def create(self, email: str, password: str, role_id: UUID) -> User:
        """
        Create a new user

        Args:
            email: User email (must be unique)
            password: Plain text password (will be hashed)
            role_id: UUID of user's role

        Returns:
            Created User instance

        Raises:
            IntegrityError: If email already exists or role_id is invalid
            ValueError: If email or password is invalid
        """
        if not email or "@" not in email:
            raise ValueError("Invalid email format")

        if not password:
            raise ValueError("Password cannot be empty")

        # Create user instance
        user = User(email=email, role_id=role_id)
        user.set_password(password)

        try:
            self.db.add(user)
            self.db.flush()
            return user
        except IntegrityError as e:
            self.db.rollback()
            if "email" in str(e).lower():
                raise ValueError(f"Email {email} already exists")
            raise

    # === READ ===

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID (includes soft-deleted users)

        Args:
            user_id: User UUID

        Returns:
            User instance or None if not found
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        """
        Get user by email

        Args:
            email: User email
            include_deleted: If False, exclude soft-deleted users

        Returns:
            User instance or None if not found
        """
        query = self.db.query(User).filter(User.email == email)

        if not include_deleted:
            query = query.filter(User.deleted_at.is_(None))

        return query.first()

    def get_all(self, include_deleted: bool = False) -> List[User]:
        """
        Get all users

        Args:
            include_deleted: If False, exclude soft-deleted users

        Returns:
            List of User instances
        """
        query = self.db.query(User)

        if not include_deleted:
            query = query.filter(User.deleted_at.is_(None))

        return query.all()

    def get_by_role(self, role_id: UUID, include_deleted: bool = False) -> List[User]:
        """
        Get all users with a specific role

        Args:
            role_id: Role UUID
            include_deleted: If False, exclude soft-deleted users

        Returns:
            List of User instances
        """
        query = self.db.query(User).filter(User.role_id == role_id)

        if not include_deleted:
            query = query.filter(User.deleted_at.is_(None))

        return query.all()

    def get_active_users(self) -> List[User]:
        """Get all active users (not soft-deleted)"""
        return self.db.query(User).filter(
            User.deleted_at.is_(None),
            User.is_active.is_(True)
        ).all()

    # === UPDATE ===

    def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """
        Update user fields (except email and password)

        Args:
            user_id: User UUID
            **kwargs: Fields to update (is_active, etc)

        Returns:
            Updated User instance or None if not found

        Raises:
            ValueError: If trying to update immutable fields (email)
        """
        if "email" in kwargs:
            raise ValueError("Email is immutable")

        if "password_hash" in kwargs:
            raise ValueError("Use set_password() to change password")

        user = self.get_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        self.db.flush()
        return user

    def change_password(self, user_id: UUID, new_password: str) -> Optional[User]:
        """
        Change user password

        Args:
            user_id: User UUID
            new_password: New plain text password

        Returns:
            Updated User instance or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.set_password(new_password)
        self.db.flush()
        return user

    # === DELETE ===

    def soft_delete(self, user_id: UUID) -> Optional[User]:
        """
        Soft-delete a user (LGPD compliance)

        Marks user as deleted but retains data for audit trail.
        Hard delete should occur 24 hours later via worker process.

        Args:
            user_id: User UUID

        Returns:
            Soft-deleted User instance or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.soft_delete()
        self.db.flush()
        return user

    def restore(self, user_id: UUID) -> Optional[User]:
        """
        Restore a soft-deleted user

        Args:
            user_id: User UUID

        Returns:
            Restored User instance or None if not found or not deleted
        """
        user = self.get_by_id(user_id)
        if not user or not user.is_deleted():
            return None

        user.restore()
        self.db.flush()
        return user

    def hard_delete(self, user_id: UUID) -> bool:
        """
        Hard-delete a user (permanent removal)

        Use only for LGPD hard-delete after 24h soft-delete window.

        Args:
            user_id: User UUID

        Returns:
            True if deleted, False if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.flush()
        return True

    # === TRANSACTION ===

    def commit(self) -> None:
        """Commit changes to database"""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback changes"""
        self.db.rollback()


__all__ = ["UserRepository"]
