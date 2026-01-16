"""add ars system prompts table

Revision ID: 003_add_ars_system_prompts
Revises: 002_add_ars_tokens
Create Date: 2026-01-16 18:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '003_add_ars_system_prompts'
down_revision = '002_add_ars_tokens'
branch_labels = None
depends_on = None


def upgrade():
    """Create ars_system_prompts table"""
    op.create_table(
        'ars_system_prompts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create index on user_id
    op.create_index('ix_ars_system_prompts_user_id', 'ars_system_prompts', ['user_id'], unique=True)


def downgrade():
    """Drop ars_system_prompts table"""
    op.drop_index('ix_ars_system_prompts_user_id', table_name='ars_system_prompts')
    op.drop_table('ars_system_prompts')
