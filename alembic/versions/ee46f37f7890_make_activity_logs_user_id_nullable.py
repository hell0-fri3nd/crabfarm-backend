"""make_activity_logs_user_id_nullable

Revision ID: ee46f37f7890
Revises: 3b6a664a5903
Create Date: 2026-07-26 16:33:54.625601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'ee46f37f7890'
down_revision: Union[str, Sequence[str], None] = '3b6a664a5903'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('activity_logs', 'user_id',
               existing_type=mysql.INTEGER(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('activity_logs', 'user_id',
               existing_type=mysql.INTEGER(),
               nullable=False)
