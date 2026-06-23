"""add_thermal_cluster_reserve_certifications_table

Revision ID: 665f7b1d7575
Revises: f50e7ed59478
Create Date: 2026-06-23 13:41:03.310148

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '665f7b1d7575'
down_revision = 'f50e7ed59478'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "thermal_reserve_certifications",
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
    op.drop_table("thermal_reserve_certifications")
