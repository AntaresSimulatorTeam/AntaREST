"""add_hydro_reserve_certifications_table

Revision ID: c7e21b9f4a83
Revises: 40f4391430e7
Create Date: 2026-08-20 10:12:44.128735

"""

from sqlalchemy import Column, Float, ForeignKeyConstraint, String

from alembic import op
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "c7e21b9f4a83"
down_revision = "40f4391430e7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hydro_reserve_certifications",
        study_data_id_col(),
        Column("area_id", String(255), nullable=False, primary_key=True),
        Column("reserve_id", String(255), nullable=False, primary_key=True),
        Column("participation_cost", Float, nullable=False),
        Column("max_release", Float, nullable=False),
        Column("max_store", Float, nullable=False),
        ForeignKeyConstraint(
            ["study_data_id", "area_id", "reserve_id"],
            ["reserve_definition.study_data_id", "reserve_definition.area_id", "reserve_definition.reserve_id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("hydro_reserve_certifications")
