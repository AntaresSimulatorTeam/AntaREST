"""add snapshot lineage versions

Revision ID: d53f532e9b78
Revises: e56b1130bc1f
Create Date: 2026-07-24 09:57:59.297868

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d53f532e9b78"
down_revision = "e56b1130bc1f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "variant_study_snapshot_lineage",
        sa.Column("snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.String(length=36), nullable=False),
        sa.Column("commands_version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["variant_study_snapshot.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("snapshot_id", "position"),
        sa.UniqueConstraint("snapshot_id", "variant_id"),
    )


def downgrade():
    op.drop_table("variant_study_snapshot_lineage")
