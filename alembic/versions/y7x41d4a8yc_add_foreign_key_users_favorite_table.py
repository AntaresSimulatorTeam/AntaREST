"""add_foreign_key_users_favorite_table

Revision ID: 6a6d36e3c6ed
Revises: f3a153a9a048
Create Date: 2026-01-26 10:45:36.111886

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey

# revision identifiers, used by Alembic.
revision = 'y7x41d4a8yc'
down_revision = '7b406752d80'
branch_labels = None
depends_on = None


def upgrade():
    # dialect_name: str = op.get_context().dialect.name
    #
    # if dialect_name == "postgresql":
    #     with op.batch_alter_table('favorite_study', schema=None) as batch_op:
    #         batch_op.create_foreign_key("fk_user_id_favorite_study", "identities", "favorite_study", ["user_id"], ["id"], ondelete="CASCADE")
    op.drop_table('favorite_study')
    op.create_table(
        "favorite_study",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("study_id", sa.String(), sa.ForeignKey("study.id", ondelete="CASCADE"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "study_id", name="pk_favorite_study"),
        sa.ForeignKeyConstraint(["user_id"], ["identities.id"], name="", ondelete="CASCADE"),
    )


def downgrade():
    op.drop_table('favorite_study')
