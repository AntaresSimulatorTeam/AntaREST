"""add output table in db

Revision ID: 6012b0407e38
Revises: 80fdf2408ede
Create Date: 2026-07-08 13:51:13.329059

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6012b0407e38'
down_revision = '80fdf2408ede'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "output",
        sa.Column("output_id", sa.String(), nullable=False),
        sa.Column("study_id", sa.String(), nullable=False),
        sa.Column("disk_space_bytes", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("output_id", "study_id", name="pk_output"),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_output_study_id", ondelete="CASCADE")
    )


def downgrade():
    op.drop_table("output")
