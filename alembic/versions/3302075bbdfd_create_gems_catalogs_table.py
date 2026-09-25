"""create_gems_catalogs_table

Revision ID: 3302075bbdfd
Revises: e12d85a77641
Create Date: 2026-09-25 09:37:53.433715

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3302075bbdfd"
down_revision = "e12d85a77641"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gems_catalogs",
        sa.Column("study_data_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("taxonomy", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("metrics_definition", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_data_id", "id"),
    )


def downgrade() -> None:
    op.drop_table("gems_catalogs")
