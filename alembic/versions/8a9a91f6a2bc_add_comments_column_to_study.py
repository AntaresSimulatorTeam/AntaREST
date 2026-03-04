"""add_comments_column_to_study

Revision ID: 8a9a91f6a2bc
Revises: 562d4e1bd95d
Create Date: 2026-03-04 11:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8a9a91f6a2bc"
down_revision = "562d4e1bd95d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("study", schema=None) as batch_op:
        batch_op.add_column(sa.Column("comments", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("study", schema=None) as batch_op:
        batch_op.drop_column("comments")
