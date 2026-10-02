"""add_reserve_definition_table

Revision ID: 7a1e9c4d82f5
Revises: c61baf008ebd
Create Date: 2026-04-15 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7a1e9c4d82f5"
down_revision = "c61baf008ebd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reserve_definition",
        sa.Column("study_id", sa.String(36), nullable=False),
        sa.Column("area_id", sa.String(255), nullable=False),
        sa.Column("reserve_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.Enum("up", "down", name="reservetype"), nullable=False),
        sa.Column("failure_cost", sa.Float(), nullable=False),
        sa.Column("spillage_cost", sa.Float(), nullable=False),
        sa.Column("reference_activation_duration", sa.Integer(), nullable=False),
        sa.Column("power_activation_ratio", sa.Float(), nullable=False),
        sa.Column("energy_activation_ratio", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "reserve_id"),
    )


def downgrade() -> None:
    op.drop_table("reserve_definition")
    sa.Enum(name="reservetype").drop(op.get_bind(), checkfirst=True)
