"""add_foreign_key_users_favorite_table

Revision ID: 6a6d36e3c6ed
Revises: f3a153a9a048
Create Date: 2026-01-26 10:45:36.111886

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'y7x41d4a8yc'
down_revision = '10318e5320f6'
branch_labels = None
depends_on = None


def upgrade():

    op.drop_table('favorite_study')
    op.create_table(
        "favorite_study",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("study_id", sa.String(36), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "study_id", name="pk_favorite_study"),
        sa.ForeignKeyConstraint(["user_id"], ["identities.id"], name="fk_user_id_favorite_study", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_study_id_favorite_study", ondelete="CASCADE")
    )


def downgrade():
    op.drop_table('favorite_study')
