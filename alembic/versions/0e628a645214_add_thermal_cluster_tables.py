"""add_thermal_cluster_tables

Revision ID: 0e628a645214
Revises: 6a6d36e3c6ed
Create Date: 2026-02-02 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0e628a645214"
down_revision = "y7x41d4a8yc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "thermal_cluster",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("thermal_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit_count", sa.Integer(), nullable=False),
        sa.Column("nominal_capacity", sa.Float(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("group", sa.String(length=255), nullable=False),
        sa.Column(
            "gen_ts",
            sa.Enum("use global", "force no generation", "force generation", name="localtsgenerationbehavior"),
            nullable=False,
        ),
        sa.Column("min_stable_power", sa.Float(), nullable=False),
        sa.Column("min_up_time", sa.Integer(), nullable=False),
        sa.Column("min_down_time", sa.Integer(), nullable=False),
        sa.Column("must_run", sa.Boolean(), nullable=False),
        sa.Column("spinning", sa.Float(), nullable=False),
        sa.Column("volatility_forced", sa.Float(), nullable=False),
        sa.Column("volatility_planned", sa.Float(), nullable=False),
        sa.Column("law_forced", sa.Enum("uniform", "geometric", name="lawoption"), nullable=False),
        sa.Column("law_planned", sa.Enum("uniform", "geometric", name="lawoption"), nullable=False),
        sa.Column("marginal_cost", sa.Float(), nullable=False),
        sa.Column("spread_cost", sa.Float(), nullable=False),
        sa.Column("fixed_cost", sa.Float(), nullable=False),
        sa.Column("startup_cost", sa.Float(), nullable=False),
        sa.Column("market_bid_cost", sa.Float(), nullable=False),
        sa.Column("co2", sa.Float(), nullable=False),
        sa.Column("nh3", sa.Float(), nullable=True),
        sa.Column("so2", sa.Float(), nullable=True),
        sa.Column("nox", sa.Float(), nullable=True),
        sa.Column("pm2_5", sa.Float(), nullable=True),
        sa.Column("pm5", sa.Float(), nullable=True),
        sa.Column("pm10", sa.Float(), nullable=True),
        sa.Column("nmvoc", sa.Float(), nullable=True),
        sa.Column("op1", sa.Float(), nullable=True),
        sa.Column("op2", sa.Float(), nullable=True),
        sa.Column("op3", sa.Float(), nullable=True),
        sa.Column("op4", sa.Float(), nullable=True),
        sa.Column("op5", sa.Float(), nullable=True),
        sa.Column(
            "cost_generation",
            sa.Enum("SetManually", "useCostTimeseries", name="thermalcostgeneration"),
            nullable=True,
        ),
        sa.Column("efficiency", sa.Float(), nullable=True),
        sa.Column("variable_o_m_cost", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_thermal_cluster_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "thermal_id", name=op.f("pk_thermal_cluster")),
    )

    op.create_table(
        "thermal_prepro",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("thermal_id", sa.String(length=255), nullable=False),
        sa.Column("matrix_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "thermal_id"],
            ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            name=op.f("fk_thermal_prepro_thermal_cluster"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "thermal_id", name=op.f("pk_thermal_prepro")),
    )

    op.create_table(
        "thermal_modulation",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("thermal_id", sa.String(length=255), nullable=False),
        sa.Column("matrix_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "thermal_id"],
            ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            name=op.f("fk_thermal_modulation_thermal_cluster"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "thermal_id", name=op.f("pk_thermal_modulation")),
    )

    op.create_table(
        "thermal_series",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("thermal_id", sa.String(length=255), nullable=False),
        sa.Column("matrix_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "thermal_id"],
            ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            name=op.f("fk_thermal_series_thermal_cluster"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "thermal_id", name=op.f("pk_thermal_series")),
    )

    op.create_table(
        "thermal_fuel_cost",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("thermal_id", sa.String(length=255), nullable=False),
        sa.Column("matrix_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "thermal_id"],
            ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            name=op.f("fk_thermal_fuel_cost_thermal_cluster"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "thermal_id", name=op.f("pk_thermal_fuel_cost")),
    )

    op.create_table(
        "thermal_co2_cost",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("thermal_id", sa.String(length=255), nullable=False),
        sa.Column("matrix_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "thermal_id"],
            ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            name=op.f("fk_thermal_co2_cost_thermal_cluster"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "thermal_id", name=op.f("pk_thermal_co2_cost")),
    )


def downgrade() -> None:
    op.drop_table("thermal_co2_cost")
    op.drop_table("thermal_fuel_cost")
    op.drop_table("thermal_series")
    op.drop_table("thermal_modulation")
    op.drop_table("thermal_prepro")
    op.drop_table("thermal_cluster")
    if op.get_context().dialect.name == "postgresql":
        sa.Enum(name="thermalcostgeneration").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="lawoption").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="localtsgenerationbehavior").drop(op.get_bind(), checkfirst=True)
