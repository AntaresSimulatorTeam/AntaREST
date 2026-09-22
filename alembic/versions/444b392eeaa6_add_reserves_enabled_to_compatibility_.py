"""add_reserves_enabled_to_compatibility_parameters

Revision ID: 444b392eeaa6
Revises: 81typ5zz6v1y
Create Date: 2026-04-03 13:45:09.584335

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '444b392eeaa6'
down_revision = '81typ5zz6v1y'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("compatibility_parameters") as batch_op:
        batch_op.add_column(sa.Column("reserves_enabled", sa.Boolean(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("compatibility_parameters") as batch_op:
        batch_op.drop_column("reserves_enabled")
