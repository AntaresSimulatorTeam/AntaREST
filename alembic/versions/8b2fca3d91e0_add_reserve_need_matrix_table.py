"""add_reserve_need_matrix_table

Revision ID: 8b2fca3d91e0
Revises: 7a1e9c4d82f5
Create Date: 2026-04-22 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "8b2fca3d91e0"
down_revision = "7a1e9c4d82f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reserve_need_matrix",
        sa.Column("study_id", sa.String(36), nullable=False),
        sa.Column("area_id", sa.String(255), nullable=False),
        sa.Column("reserve_id", sa.String(255), nullable=False),
        sa.Column("matrix_id", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "reserve_id"],
            ["reserve_definition.study_id", "reserve_definition.area_id", "reserve_definition.reserve_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "reserve_id"),
    )


def downgrade() -> None:
    op.drop_table("reserve_need_matrix")
