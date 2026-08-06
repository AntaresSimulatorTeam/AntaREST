"""add output table in db

Revision ID: 6012b0407e38
Revises: 06697016d057
Create Date: 2026-07-08 13:51:13.329059

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6012b0407e38"
down_revision = "06697016d057"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "output",
        sa.Column("study_id", sa.String(), nullable=False),
        sa.Column("output_id", sa.String(), nullable=False),
        sa.Column("disk_space_bytes", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("study_id", "output_id", name="pk_output"),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_output_study_id", ondelete="CASCADE"),
    )


def downgrade():
    op.drop_table("output")
