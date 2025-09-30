"""Create initial database schema for single organization

Revision ID: 001_initial_single_org
Revises: 
Create Date: 2025-09-30 19:00:00.000000

Creates tables for single organization:
- users table (authentication and authorization)
- chat_sessions table (session management)
- chat_messages table (message history)
- chat_metadata table (session metadata)
- chat_history_stats table (statistics)

No multi-tenant support - single organization only.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_initial_single_org'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema"""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_role', 'users', ['role'])
    
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id_int', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
        sa.ForeignKeyConstraint(['user_id_int'], ['users.id'], ondelete='SET NULL'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_chat_sessions_id', 'chat_sessions', ['id'])
    op.create_index('ix_chat_sessions_session_id', 'chat_sessions', ['session_id'], unique=True)
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('ix_chat_sessions_user_id_int', 'chat_sessions', ['user_id_int'])
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', mysql.LONGTEXT(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False, default='text'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('source_documents', sa.JSON(), nullable=True),
        sa.Column('error_info', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_chat_messages_id', 'chat_messages', ['id'])
    op.create_index('ix_chat_messages_message_id', 'chat_messages', ['message_id'], unique=True)
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_role', 'chat_messages', ['role'])
    
    # Create chat_metadata table
    op.create_table(
        'chat_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('total_messages', sa.Integer(), nullable=False, default=0),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('last_user_message', sa.String(length=255), nullable=True),
        sa.Column('last_assistant_message', sa.String(length=255), nullable=True),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False, default='ja'),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('custom_fields', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_chat_metadata_id', 'chat_metadata', ['id'])
    op.create_index('ix_chat_metadata_session_id', 'chat_metadata', ['session_id'], unique=True)
    
    # Create chat_history_stats table
    op.create_table(
        'chat_history_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.String(length=10), nullable=False),
        sa.Column('total_sessions', sa.Integer(), nullable=False, default=0),
        sa.Column('total_messages', sa.Integer(), nullable=False, default=0),
        sa.Column('total_users', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_session_length', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_chat_history_stats_id', 'chat_history_stats', ['id'])
    op.create_index('ix_chat_history_stats_date', 'chat_history_stats', ['date'], unique=True)


def downgrade() -> None:
    """Downgrade database schema"""
    
    # Drop tables in reverse order
    op.drop_index('ix_chat_history_stats_date', table_name='chat_history_stats')
    op.drop_index('ix_chat_history_stats_id', table_name='chat_history_stats')
    op.drop_table('chat_history_stats')
    
    op.drop_index('ix_chat_metadata_session_id', table_name='chat_metadata')
    op.drop_index('ix_chat_metadata_id', table_name='chat_metadata')
    op.drop_table('chat_metadata')
    
    op.drop_index('ix_chat_messages_role', table_name='chat_messages')
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_message_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    
    op.drop_index('ix_chat_sessions_user_id_int', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_user_id', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_session_id', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_id', table_name='chat_sessions')
    op.drop_table('chat_sessions')
    
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')
