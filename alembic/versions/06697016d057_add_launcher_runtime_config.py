"""add launcher_runtime_config

Revision ID: 06697016d057
Revises: 3855b61c3232
Create Date: 2026-08-03 11:24:03.839320

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "06697016d057"
down_revision = "3855b61c3232"
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
