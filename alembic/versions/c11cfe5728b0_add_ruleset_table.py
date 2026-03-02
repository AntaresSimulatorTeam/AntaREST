"""add scenario builder tables

Revision ID: c11cfe5728b0
Revises: 562d4e1bd95d
Create Date: 2026-02-24 09:10:06.132523

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c11cfe5728b0"
down_revision = "562d4e1bd95d"
branch_labels = None
depends_on = None

_AREA_SCENARIO_TABLES = [
    "scenario_load",
    "scenario_hydro",
    "scenario_wind",
    "scenario_solar",
    "scenario_hydro_initial_level",
    "scenario_hydro_final_level",
    "scenario_hydro_generation_power",
]

_ALL_TABLES = [
    *_AREA_SCENARIO_TABLES,
    "scenario_ntc",
    "scenario_binding_constraints",
    "scenario_thermal",
    "scenario_renewable",
    "scenario_storage_inflows",
    "scenario_storage_constraints",
]


def upgrade() -> None:
    # Area scenario tables (7 tables with same structure)
    for table_name in _AREA_SCENARIO_TABLES:
        op.create_table(
            table_name,
            sa.Column("study_id", sa.String(length=36), nullable=False),
            sa.Column("area_id", sa.String(length=255), nullable=False),
            sa.Column("timeseries", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("study_id", "area_id"),
        )

    op.create_table(
        "scenario_ntc",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area1", sa.String(length=255), nullable=False),
        sa.Column("area2", sa.String(length=255), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area1", "area2"],
            ["link.study_id", "link.area1", "link.area2"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area1", "area2"),
    )

    op.create_table(
        "scenario_binding_constraints",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("bc_group_id", sa.String(length=255), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", "bc_group_id"),
    )

    op.create_table(
        "scenario_thermal",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("thermal_id", sa.String(length=255), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "thermal_id"],
            ["thermal_cluster.study_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "thermal_id"),
    )

    op.create_table(
        "scenario_renewable",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("renewable_id", sa.String(length=255), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "renewable_id"],
            ["renewable_cluster.study_id", "renewable_cluster.area_id", "renewable_cluster.renewable_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "renewable_id"),
    )

    op.create_table(
        "scenario_storage_inflows",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("st_storage_id", sa.String(length=255), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "st_storage_id"],
            ["st_storage.study_id", "st_storage.area_id", "st_storage.st_storage_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "st_storage_id"),
    )

    op.create_table(
        "scenario_storage_constraints",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("st_storage_id", sa.String(length=255), nullable=False),
        sa.Column("constraint_id", sa.String(length=255), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "st_storage_id", "constraint_id"],
            [
                "st_storage_additional_constraint.study_id",
                "st_storage_additional_constraint.area_id",
                "st_storage_additional_constraint.st_storage_id",
                "st_storage_additional_constraint.constraint_id",
            ],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "st_storage_id", "constraint_id"),
    )


def downgrade() -> None:
    for table_name in reversed(_ALL_TABLES):
        op.drop_table(table_name)
