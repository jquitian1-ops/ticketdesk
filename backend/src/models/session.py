"""Session entity - Interview session tracking"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from . import Base


class Session(Base):
    """
    Session Aggregate - Interview session tracking

    Tracks candidate interview sessions with soft-delete support for LGPD compliance.
    """
    __tablename__ = "sessions"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_email = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    session_data = Column(Text, nullable=True, default="{}")  # JSON

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # LGPD soft-delete

    # Relationships
    account = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session(id={self.id}, account_id={self.account_id}, status='{self.status}')>"
