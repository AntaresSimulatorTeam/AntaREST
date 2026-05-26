"""drop_reserve_definition_name

Revision ID: b2f7e9a1c4d3
Revises: 7a1e9c4d82f5
Create Date: 2026-04-22 15:30:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2f7e9a1c4d3"
down_revision = "7a1e9c4d82f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("reserve_definition") as batch_op:
        batch_op.drop_column("name")


def downgrade() -> None:
    with op.batch_alter_table("reserve_definition") as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(255), nullable=False))
