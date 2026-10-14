"""create_gems_data_series_table

Revision ID: 18577b807e19
Revises: f2e3f7ba9896
Create Date: 2026-10-14 09:30:00.000000

"""

import sqlalchemy as sa

from alembic import op
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "18577b807e19"
down_revision = "f2e3f7ba9896"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gems_data_series",
        study_data_id_col(primary_key=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("values", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_data_id"], ["study_data.study_data_id"], name="fk_gems_data_series_study_data", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("study_data_id", "id", name="pk_gems_data_series"),
    )


def downgrade() -> None:
    op.drop_table("gems_data_series")
