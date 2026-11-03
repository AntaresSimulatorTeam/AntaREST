"""add hydro rule curves and daily reservoir level tables

Revision ID: e3f1a8c04b27
Revises: 193aa1d7b5ad
Create Date: 2026-10-29 16:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy import Column, String

from alembic import op
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "e3f1a8c04b27"
down_revision = "193aa1d7b5ad"
branch_labels = None
depends_on = None

_TABLES = (
    "hydro_max_daily_reservoir_levels",
    "hydro_min_daily_reservoir_levels",
    "hydro_avg_daily_reservoir_levels",
)


def upgrade() -> None:
    hydro_rule_curves_enum = sa.Enum("scenarized", "single", name="hydrorulecurves")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        hydro_rule_curves_enum.create(bind, checkfirst=True)

    with op.batch_alter_table("compatibility_parameters") as batch_op:
        batch_op.add_column(sa.Column("hydro_rule_curves", hydro_rule_curves_enum, nullable=True))

    for table_name in _TABLES:
        op.create_table(
            table_name,
            study_data_id_col(),
            Column("area_id", String(255), nullable=False, primary_key=True),
            Column("matrix_id", String(64), nullable=False),
        )


def downgrade() -> None:
    for table_name in reversed(_TABLES):
        op.drop_table(table_name)

    with op.batch_alter_table("compatibility_parameters") as batch_op:
        batch_op.drop_column("hydro_rule_curves")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="hydrorulecurves").drop(bind, checkfirst=True)
