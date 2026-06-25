"""create_thermal_symmetries_table

Revision ID: c88bcff025ef
Revises: 665f7b1d7575
Create Date: 2026-06-25 16:46:25.924042

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c88bcff025ef'
down_revision = '665f7b1d7575'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "thermal_reserve_symmetries",
        sa.Column("study_id", sa.String(36), nullable=False),
        sa.Column("area_id", sa.String(255), nullable=False),
        sa.Column("thermal_id", sa.String(255), nullable=False),
        sa.Column("symmetries", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "thermal_id"],
            ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "thermal_id"),
    )


def downgrade() -> None:
    op.drop_table("thermal_reserve_symmetries")
