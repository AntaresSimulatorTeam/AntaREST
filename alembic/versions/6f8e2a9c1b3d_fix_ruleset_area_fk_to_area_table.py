"""fix ruleset area foreign keys

Revision ID: 6f8e2a9c1b3d
Revises: 8a9a91f6a2bc
Create Date: 2026-03-09 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6f8e2a9c1b3d"
down_revision = "8a9a91f6a2bc"
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


def _rebuild_area_scenario_table(table_name: str, reference_area: bool) -> None:
    tmp_table_name = f"{table_name}_tmp_fk_fix"
    columns = ["study_id", "area_id", "value"]
    foreign_key = (
        sa.ForeignKeyConstraint(("study_id", "area_id"), ["area.study_id", "area.area_id"], ondelete="CASCADE")
        if reference_area
        else sa.ForeignKeyConstraint(("study_id",), ["study.id"], ondelete="CASCADE")
    )

    op.create_table(
        tmp_table_name,
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        foreign_key,
        sa.PrimaryKeyConstraint("study_id", "area_id"),
    )
    source_table = sa.table(table_name, *(sa.column(column_name) for column_name in columns))
    tmp_table = sa.table(tmp_table_name, *(sa.column(column_name) for column_name in columns))
    op.execute(sa.insert(tmp_table).from_select(columns, sa.select(*(source_table.c[column_name] for column_name in columns))))
    op.drop_table(table_name)
    op.rename_table(tmp_table_name, table_name)


def upgrade() -> None:
    for table_name in _AREA_SCENARIO_TABLES:
        _rebuild_area_scenario_table(table_name, reference_area=True)


def downgrade() -> None:
    for table_name in _AREA_SCENARIO_TABLES:
        _rebuild_area_scenario_table(table_name, reference_area=False)
