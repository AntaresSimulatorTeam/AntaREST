"""adding favorite table

Revision ID: 7b406752d80
Revises: 0146b79f723c
Create Date: 2026-01-07 10:27:58.254977

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "7b406752d80"
down_revision = "0146b79f723c"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "favorite",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("study_id", sa.String(), sa.ForeignKey("study.id"), nullable=False, ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "study_id", name="pk_favorite"),
    )

def downgrade():
    op.drop_constraint("pk_favorite", "favorite", type_="primary")
    op.drop_table("favorite")