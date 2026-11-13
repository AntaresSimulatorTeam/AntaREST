"""create_output_gems_views_table

Revision ID: c4d7e9a1f3b2
Revises: b8e5c1a7d902
Create Date: 2026-11-13 12:04:01.956744

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c4d7e9a1f3b2"
down_revision = "b8e5c1a7d902"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "output_gems_views",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("output_id", sa.String(), nullable=False),
        sa.Column("views_version", sa.Integer(), nullable=False),
        sa.Column("views", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name="fk_output_gems_views_study_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "output_id"),
    )


def downgrade() -> None:
    op.drop_table("output_gems_views")
