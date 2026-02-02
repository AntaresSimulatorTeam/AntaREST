"""add_layer_table

Revision ID: 9c4e7f2a3b1d
Revises: y7x41d4a8yc
Create Date: 2026-01-29 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9c4e7f2a3b1d"
down_revision = "y7x41d4a8yc"
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

    with op.batch_alter_table("area_ui") as batch_op:
        batch_op.create_foreign_key(
            op.f("fk_area_ui_study_id_layer_id_layer"),
            "layer",
            ["study_id", "layer_id"],
            ["study_id", "layer_id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("area_ui") as batch_op:
        batch_op.drop_constraint(op.f("fk_area_ui_study_id_layer_id_layer"), type_="foreignkey")
    op.drop_table("layer")
