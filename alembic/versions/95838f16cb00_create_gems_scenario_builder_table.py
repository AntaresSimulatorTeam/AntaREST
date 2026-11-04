"""create_gems_scenario_builder_table

Revision ID: 95838f16cb00
Revises: e6892cbcad66
Create Date: 2026-09-18 16:36:03.902782

"""

from alembic import op
import sqlalchemy as sa

from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "95838f16cb00"
down_revision = "e6892cbcad66"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gems_scenario_builder",
        study_data_id_col(),
        sa.Column("scenario_group", sa.String(255), primary_key=True),
        sa.Column("data", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("gems_scenario_builder")
