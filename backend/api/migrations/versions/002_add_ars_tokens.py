"""add ars tokens table

Revision ID: 002
Revises: 001
Create Date: 2026-01-16 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002_add_ars_tokens'
down_revision = '001_initial_single_org'
branch_labels = None
depends_on = None


def upgrade():
    """Create api_ars_tokens table"""
    op.create_table(
        'api_ars_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_type', sa.String(16), nullable=False, server_default='token'),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('ix_api_ars_tokens_id', 'api_ars_tokens', ['id'])
    op.create_index('ix_api_ars_tokens_user_id', 'api_ars_tokens', ['user_id'])


def downgrade():
    """Drop api_ars_tokens table"""
    op.drop_index('ix_api_ars_tokens_user_id', 'api_ars_tokens')
    op.drop_index('ix_api_ars_tokens_id', 'api_ars_tokens')
    op.drop_table('api_ars_tokens')
