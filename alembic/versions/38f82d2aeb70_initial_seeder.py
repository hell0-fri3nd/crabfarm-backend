"""initial seeder

Revision ID: 38f82d2aeb70
Revises: 4c7a304e1009
Create Date: 2026-01-11 20:36:03.414615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c773fe41d7f'
down_revision: Union[str, Sequence[str], None] = '4c7a304e1009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    users_table = sa.table(
        "users",
        sa.column("email", sa.String),
        sa.column("password", sa.String)
    )
    
    op.bulk_insert(
        users_table,
        [
            {
                "email": "hellofriend@gmail.com",
                "password": "hellofriend"
            }
        ],
    )
    
    crab_table = sa.table(
        "crab",
        sa.column("name", sa.String),
        sa.column("group_by", sa.String)
    )
    
    op.bulk_insert(
        crab_table,
        [
            {
                "name": "A1_Crab",
                "group_by": "A"
            },
            {
                "name": "A2_Crab",
                "group_by": "A"
            },
            {
                "name": "A3_Crab",
                "group_by": "A"
            },
            {
                "name": "A4_Crab",
                "group_by": "A"
            },
            
            {
                "name": "B1_Crab",
                "group_by": "B"
            },
            {
                "name": "B2_Crab",
                "group_by": "B"
            },
            {
                "name": "B3_Crab",
                "group_by": "B"
            },
            {
                "name": "B4_Crab",
                "group_by": "B"
            },
            
            {
                "name": "C1_Crab",
                "group_by": "C"
            },
            {
                "name": "C2_Crab",
                "group_by": "C"
            },
            {
                "name": "C3_Crab",
                "group_by": "C"
            },
            {
                "name": "C4_Crab",
                "group_by": "C"
            },
            
            {
                "name": "D1_Crab",
                "group_by": "D"
            },
            {
                "name": "D2_Crab",
                "group_by": "D"
            },
            {
                "name": "D3_Crab",
                "group_by": "D"
            },
            {
                "name": "D4_Crab",
                "group_by": "D"
            }
        ],
    )
        
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM users WHERE email = 'hellofriend@gmail.com'")
    op.execute("""
        TRUNCATE TABLE crab
    """)
    pass
