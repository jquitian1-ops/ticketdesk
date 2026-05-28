"""Initial database schema for TicketDesk Enterprise - Unit 1 + Unit 6

Revision ID: 001
Revises:
Create Date: 2026-05-27

Tables created:
- users: User accounts with role-based access control
- roles: Role definitions with permissions
- sessions: Interview session tracking with soft-delete (LGPD)
- audit_logs: 100% event audit trail for compliance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema tables and indexes"""

    # 1. ROLES TABLE
    # Stores role definitions (admin, recruiter, candidate)
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('permissions', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='roles_name_uq'),
    )

    # 2. USERS TABLE
    # Core user aggregate (email, password, role, LGPD soft-delete)
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='users_role_id_fk'),
        sa.UniqueConstraint('email', name='users_email_uq'),
    )

    # 3. SESSIONS TABLE
    # Interview session tracking with soft-delete (LGPD <24h SLA)
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_email', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['users.id'], name='sessions_account_id_fk', ondelete='CASCADE'),
    )

    # 4. AUDIT_LOGS TABLE
    # 100% event traceability for LGPD compliance
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('changes', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='audit_logs_user_id_fk', ondelete='CASCADE'),
    )

    # INDEXES for performance
    # Email lookup (login authentication)
    op.create_index('users_email_idx', 'users', ['email'], unique=False)

    # Session filtering by account
    op.create_index('sessions_account_id_idx', 'sessions', ['account_id'], unique=False)

    # Session status filtering (pending, completed, etc.)
    op.create_index('sessions_status_idx', 'sessions', ['status'], unique=False)

    # Soft-delete queries (LGPD hard-delete worker)
    op.create_index('sessions_deleted_at_idx', 'sessions', ['deleted_at'], unique=False)
    op.create_index('users_deleted_at_idx', 'users', ['deleted_at'], unique=False)

    # Audit log filtering
    op.create_index('audit_logs_user_id_idx', 'audit_logs', ['user_id'], unique=False)
    op.create_index('audit_logs_resource_idx', 'audit_logs', ['resource', 'resource_id'], unique=False)
    op.create_index('audit_logs_created_at_idx', 'audit_logs', ['created_at'], unique=False)

    print("✅ Initial schema created successfully")
    print("   - roles (role-based access control)")
    print("   - users (with LGPD soft-delete support)")
    print("   - sessions (interview tracking with soft-delete)")
    print("   - audit_logs (100% compliance audit trail)")
    print("   - 8 indexes for optimal query performance")


def downgrade() -> None:
    """Drop all tables created in upgrade"""

    # Drop indexes first
    op.drop_index('audit_logs_created_at_idx', table_name='audit_logs')
    op.drop_index('audit_logs_resource_idx', table_name='audit_logs')
    op.drop_index('audit_logs_user_id_idx', table_name='audit_logs')
    op.drop_index('users_deleted_at_idx', table_name='users')
    op.drop_index('sessions_deleted_at_idx', table_name='sessions')
    op.drop_index('sessions_status_idx', table_name='sessions')
    op.drop_index('sessions_account_id_idx', table_name='sessions')
    op.drop_index('users_email_idx', table_name='users')

    # Drop tables (in reverse order of creation due to FKs)
    op.drop_table('audit_logs')
    op.drop_table('sessions')
    op.drop_table('users')
    op.drop_table('roles')

    print("✅ Schema rolled back successfully")
