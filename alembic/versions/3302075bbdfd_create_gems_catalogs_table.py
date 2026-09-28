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
        sa.ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_data_id", "id"),
    )
    op.create_table(
        "gems_catalog_metrics",
        sa.Column("study_data_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("catalog_id", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("terms_operator", sa.String(length=255), nullable=False),
        sa.Column("time_operator", sa.String(length=255), nullable=False),
        sa.Column("terms", sa.String(), nullable=True),
        sa.Column("breakdown", sa.String(), nullable=True),
        sa.Column("filter", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_data_id", "catalog_id"], ["gems_catalogs.study_data_id", "gems_catalogs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("study_data_id", "catalog_id", "id"),
    )


def downgrade() -> None:
    op.drop_table("gems_catalog_metrics")
    op.drop_table("gems_catalogs")
