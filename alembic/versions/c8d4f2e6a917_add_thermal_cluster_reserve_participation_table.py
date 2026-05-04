"""add_thermal_cluster_reserve_participation_table

Revision ID: c8d4f2e6a917
Revises: 8b2fca3d91e0
Create Date: 2026-05-04 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c8d4f2e6a917"
down_revision = "8b2fca3d91e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "thermal_cluster_reserve_participation",
        sa.Column("study_id", sa.String(36), nullable=False),
        sa.Column("area_id", sa.String(255), nullable=False),
        sa.Column("thermal_id", sa.String(255), nullable=False),
        sa.Column("reserve_id", sa.String(255), nullable=False),
        sa.Column("max_power", sa.Float(), nullable=False),
        sa.Column("max_power_off", sa.Float(), nullable=False),
        sa.Column("participation_cost", sa.Float(), nullable=False),
        sa.Column("participation_cost_off", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "thermal_id"],
            ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "reserve_id"],
            ["reserve_definition.study_id", "reserve_definition.area_id", "reserve_definition.reserve_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "thermal_id", "reserve_id"),
    )


def downgrade() -> None:
    op.drop_table("thermal_cluster_reserve_participation")
