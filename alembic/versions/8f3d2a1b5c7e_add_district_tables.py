"""add_district_tables

Revision ID: 8f3d2a1b5c7e
Revises: 2572145aff71
Create Date: 2026-01-26 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision = "8f3d2a1b5c7e"
down_revision = "2572145aff71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "district",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("district_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("output", sa.Boolean(), nullable=False),
        sa.Column("comments", sa.String(length=500), nullable=False),
        sa.Column("apply_filter", sa.Enum("add-all", "remove-all", name="districtapplyfilter"), nullable=False),
        sa.Column("add_areas", String(), nullable=False),
        sa.Column("subtract_areas", String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_district_study_id_study"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "district_id", name=op.f("pk_district")),
    )


def downgrade() -> None:
    op.drop_table("district")
    sa.Enum(name="districtapplyfilter").drop(op.get_bind(), checkfirst=True)