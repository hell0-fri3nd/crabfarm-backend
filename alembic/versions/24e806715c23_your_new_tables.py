"""your new tables

Revision ID: 24e806715c23
Revises: aefb5bbab48e
Create Date: 2026-05-03 15:20:33.365498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24e806715c23'
down_revision: Union[str, Sequence[str], None] = 'aefb5bbab48e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    users_table = sa.table(
        "users",
        sa.column("name", sa.String), 
        sa.column("email", sa.String),
        sa.column("password", sa.String),
        sa.column("pin", sa.String),
        sa.column("roles", sa.String)  # add this
    )
    
    op.bulk_insert(
        users_table,
        [
            {
                "name": "Hello Friend",
                "email": "hellofriend@gmail.com",
                "password": "hellofriend",
                "pin": "1234",
                "roles": "admin"
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
            # A GROUP
            {
                "name": "A1 CRAB",
                "group_by": "A"
            },
            {
                "name": "A2 CRAB",
                "group_by": "A"
            },
            {
                "name": "A3 CRAB",
                "group_by": "A"
            },
            {
                "name": "A4 CRAB",
                "group_by": "A"
            },
            {
                "name": "A5 CRAB",
                "group_by": "A"
            },
            
            # B GROUP
            {
                "name": "B1 CRAB",
                "group_by": "B"
            },
            {
                "name": "B2 CRAB",
                "group_by": "B"
            },
            {
                "name": "B3 CRAB",
                "group_by": "B"
            },
            {
                "name": "B4 CRAB",
                "group_by": "B"
            },
            {
                "name": "B5 CRAB",
                "group_by": "B"
            },
            
            # C GROUP
            {
                "name": "C1 CRAB",
                "group_by": "C"
            },
            {
                "name": "C2 CRAB",
                "group_by": "C"
            },
             {
                "name": "C3 CRAB",
                "group_by": "C"
            },
            {
                "name": "C4 CRAB",
                "group_by": "C"
            },
            {
                "name": "C5 CRAB",
                "group_by": "C"
            },
            
            # D GROUP
            {
                "name": "D1 GROUP",
                "group_by": "D"
            },
            {
                "name": "D2 GROUP",
                "group_by": "D"
            },
            {
                "name": "D3 GROUP",
                "group_by": "D"
            },
            {
                "name": "D4 GROUP",
                "group_by": "D"
            },
            {
                "name": "D5 GROUP",
                "group_by": "D"
            },
            
            # E GROUP
            {
                "name": "E1 GROUP",
                "group_by": "E"
            },
            {
                "name": "E2 GROUP",
                "group_by": "E"
            },
            {
                "name": "E3 GROUP",
                "group_by": "E"
            },
            {
                "name": "E4 GROUP",
                "group_by": "E"
            },
            {
                "name": "E5 GROUP",
                "group_by": "E"
            }
        ],
    )
        
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM users WHERE email = 'hellofriend@gmail.com'")
    op.execute("""
        TRUNCATE TABLE crab
    """)
    pass
