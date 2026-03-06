"""add_comments_table

Revision ID: 8a9a91f6a2bc
Revises: c11cfe5728b0
Create Date: 2026-03-04 11:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8a9a91f6a2bc"
down_revision = "c11cfe5728b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("comments", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id"),
    )


def downgrade() -> None:
    op.drop_table("comments")
