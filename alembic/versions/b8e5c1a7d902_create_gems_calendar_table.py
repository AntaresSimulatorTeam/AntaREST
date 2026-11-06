"""create_gems_calendar_table

Revision ID: b8e5c1a7d902
Revises: e3f1a8c04b27
Create Date: 2026-11-06 11:15:00.000000

"""

from alembic import op
import sqlalchemy as sa

from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "b8e5c1a7d902"
down_revision = "e3f1a8c04b27"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gems_calendar",
        study_data_id_col(),
        sa.Column("calendar", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_data_id"],
            ["study_data.study_data_id"],
            name="fk_gems_calendar_study_data",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_data_id", name="pk_gems_calendar"),
    )


def downgrade() -> None:
    op.drop_table("gems_calendar")
