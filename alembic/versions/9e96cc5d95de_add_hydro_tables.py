"""add_hydro_tables

Revision ID: 9e96cc5d95de
Revises: 0e628a645214
Create Date: 2026-02-10 11:28:30.653492

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9e96cc5d95de"
down_revision = "0e628a645214"
branch_labels = None
depends_on = None


def upgrade():
    # hydro_management table
    op.create_table(
        "hydro_management",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("inter_daily_breakdown", sa.Float, nullable=False),
        sa.Column("intra_daily_modulation", sa.Float, nullable=False),
        sa.Column("inter_monthly_breakdown", sa.Float, nullable=False),
        sa.Column("reservoir", sa.Boolean, nullable=False),
        sa.Column("reservoir_capacity", sa.Float, nullable=False),
        sa.Column("follow_load", sa.Boolean, nullable=False),
        sa.Column("use_water", sa.Boolean, nullable=False),
        sa.Column("hard_bounds", sa.Boolean, nullable=False),
        sa.Column("initialize_reservoir_date", sa.Integer, nullable=False),
        sa.Column("use_heuristic", sa.Boolean, nullable=False),
        sa.Column("power_to_level", sa.Boolean, nullable=False),
        sa.Column("use_leeway", sa.Boolean, nullable=False),
        sa.Column("leeway_low", sa.Float, nullable=False),
        sa.Column("leeway_up", sa.Float, nullable=False),
        sa.Column("pumping_efficiency", sa.Float, nullable=False),
        sa.Column("overflow_spilled_cost_difference", sa.Float, nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_hydro_management_study_id_area_id_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f("pk_hydro_management")),
    )

    # hydro_inflow_structure table
    op.create_table(
        "hydro_inflow_structure",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("inter_monthly_correlation", sa.Float, nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_hydro_inflow_structure_study_id_area_id_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f("pk_hydro_inflow_structure")),
    )

    # hydro_allocation table
    op.create_table(
        "hydro_allocation",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("source_area_id", sa.String(length=255), nullable=False),
        sa.Column("target_area_id", sa.String(length=255), nullable=False),
        sa.Column("coefficient", sa.Float, nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "source_area_id"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_hydro_allocation_study_id_source_area_id_area"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["study_id", "target_area_id"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_hydro_allocation_study_id_target_area_id_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "source_area_id", "target_area_id", name=op.f("pk_hydro_allocation")),
    )

    # hydro_correlation table
    op.create_table(
        "hydro_correlation",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_from", sa.String(length=255), nullable=False),
        sa.Column("area_to", sa.String(length=255), nullable=False),
        sa.Column("coefficient", sa.Float, nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_from"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_hydro_correlation_study_id_area_from_area"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["study_id", "area_to"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_hydro_correlation_study_id_area_to_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_from", "area_to", name=op.f("pk_hydro_correlation")),
    )


def downgrade():
    op.drop_table("hydro_correlation")
    op.drop_table("hydro_allocation")
    op.drop_table("hydro_inflow_structure")
    op.drop_table("hydro_management")
