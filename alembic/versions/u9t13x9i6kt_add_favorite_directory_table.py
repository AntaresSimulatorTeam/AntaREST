"""add_favorite_directory_table

Revision ID: 6a6d36e3c6ed
Revises: 6a6d36e3c6ed
Create Date: 2026-01-26 10:45:36.111886

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'u9t13x9i6kt'
down_revision = '124274d80f2e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "favorite_directory",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("directory_id", sa.String(36), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "directory_id", name="pk_favorite_directory"),
        sa.ForeignKeyConstraint(["user_id"], ["identities.id"], name="fk_user_id_favorite_study", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["directory_id"], ["directory.id"], name="fk_directory_id", ondelete="CASCADE"),
    )


def downgrade():
    op.drop_table("favorite_directory")