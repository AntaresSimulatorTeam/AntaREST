"""add_hydro_matrix_tables

Revision ID: ae838d5fd166b
Revises: ae838d5fd166
Create Date: 2026-02-17 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ae838d5fd166b"
down_revision = "ae838d5fd166"
branch_labels = None
depends_on = None

_HYDRO_MATRIX_TABLES = [
    "hydro_maxpower",
    "hydro_reservoir",
    "hydro_energy",
    "hydro_run_of_river",
    "hydro_modulation",
    "hydro_credit_modulations",
    "hydro_inflow_pattern",
    "hydro_water_values",
    "hydro_mingen",
    "hydro_max_hourly_gen_power",
    "hydro_max_hourly_pump_power",
    "hydro_max_daily_gen_energy",
    "hydro_max_daily_pump_energy",
]


def upgrade():
    for table_name in _HYDRO_MATRIX_TABLES:
        op.create_table(
            table_name,
            sa.Column("study_id", sa.String(length=36), nullable=False),
            sa.Column("area_id", sa.String(length=255), nullable=False),
            sa.Column("matrix_id", sa.String(length=64), nullable=False),
            sa.ForeignKeyConstraint(
                ["study_id", "area_id"],
                ["area.study_id", "area.area_id"],
                name=op.f(f"fk_{table_name}_study_id_area_id_area"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f(f"pk_{table_name}")),
        )


def downgrade():
    for table_name in reversed(_HYDRO_MATRIX_TABLES):
        op.drop_table(table_name)
