"""add hydro daily reservoir level tables

Revision ID: e3f1a8c04b27
Revises: c7e2a91f4d38
Create Date: 2026-10-29 16:00:00.000000

"""

from sqlalchemy import Column, ForeignKeyConstraint, String

from alembic import op
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "e3f1a8c04b27"
down_revision = "c7e2a91f4d38"
branch_labels = None
depends_on = None

_TABLES = (
    "hydro_max_daily_reservoir_levels",
    "hydro_min_daily_reservoir_levels",
    "hydro_avg_daily_reservoir_levels",
)


def upgrade() -> None:
    for table_name in _TABLES:
        op.create_table(
            table_name,
            study_data_id_col(),
            Column("area_id", String(255), nullable=False, primary_key=True),
            Column("matrix_id", String(64), nullable=False),
            ForeignKeyConstraint(
                ["study_data_id", "area_id"],
                ["area.study_data_id", "area.area_id"],
                ondelete="CASCADE",
            ),
        )


def downgrade() -> None:
    for table_name in reversed(_TABLES):
        op.drop_table(table_name)
