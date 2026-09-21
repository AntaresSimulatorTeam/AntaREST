"""create_gems_scenario_builder_table

Revision ID: 95838f16cb00
Revises: e6892cbcad66
Create Date: 2026-09-18 16:36:03.902782

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "95838f16cb00"
down_revision = "e6892cbcad66"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gems_scenario_builder",
        sa.Column("study_data_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("scenario_groups", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_data_id"),
    )


def downgrade() -> None:
    op.drop_table("gems_scenario_builder")
