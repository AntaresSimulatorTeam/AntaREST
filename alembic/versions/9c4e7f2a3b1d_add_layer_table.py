"""add_layer_table

Revision ID: 9c4e7f2a3b1d
Revises: 8f3d2a1b5c7e
Create Date: 2026-01-29 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9c4e7f2a3b1d"
down_revision = "8f3d2a1b5c7e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "layer",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("layer_id", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_layer_study_id_study"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "layer_id", name=op.f("pk_layer")),
    )


def downgrade() -> None:
    op.drop_table("layer")
