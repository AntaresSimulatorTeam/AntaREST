"""Add launcher_runtime_config table

Revision ID: ant5114a1b2c3
Revises: 665f7b1d7575
Create Date: 2026-07-23 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ant5114a1b2c3"
down_revision = "665f7b1d7575"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "launcher_runtime_config",
        sa.Column("launcher_id", sa.String(length=36), nullable=False),
        sa.Column("oversubscribe_core_threshold", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("launcher_id"),
    )


def downgrade():
    op.drop_table("launcher_runtime_config")
