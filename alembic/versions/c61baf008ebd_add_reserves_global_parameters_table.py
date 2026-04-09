"""add_reserves_global_parameters_table

Revision ID: c61baf008ebd
Revises: 444b392eeaa6
Create Date: 2026-04-09 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c61baf008ebd"
down_revision = "444b392eeaa6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reserves_global_parameters",
        sa.Column("study_id", sa.String(36), nullable=False),
        sa.Column("area_id", sa.String(255), nullable=False),
        sa.Column("reference_activation_duration_up", sa.Integer(), nullable=False),
        sa.Column("energy_activation_ratio_up", sa.Float(), nullable=False),
        sa.Column("reference_activation_duration_down", sa.Integer(), nullable=False),
        sa.Column("energy_activation_ratio_down", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id"),
    )


def downgrade() -> None:
    op.drop_table("reserves_global_parameters")
