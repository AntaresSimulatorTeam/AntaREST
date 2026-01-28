"""add_district_tables

Revision ID: 8f3d2a1b5c7e
Revises: 2572145aff71
Create Date: 2026-01-26 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8f3d2a1b5c7e"
down_revision = "2572145aff71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create district table
    op.create_table(
        "district",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("district_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("output", sa.Boolean(), nullable=False),
        sa.Column("comments", sa.String(length=500), nullable=False),
        sa.Column("apply_filter", sa.Enum("add-all", "remove-all", name="districtapplyfilter"), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_district_study_id_study"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "district_id", name=op.f("pk_district")),
    )

    # 2. Create district_area table (junction table for add_areas and subtract_areas)
    op.create_table(
        "district_area",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("district_id", sa.String(length=255), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "district_id"],
            ["district.study_id", "district.district_id"],
            name=op.f("fk_district_area_study_id_district_id_district"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_district_area_study_id_area_id_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "district_id", "area_id", "mode", name=op.f("pk_district_area")),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("district_area")
    op.drop_table("district")
    # Drop enum type (required for PostgreSQL)
    sa.Enum(name="districtapplyfilter").drop(op.get_bind(), checkfirst=True)