"""add_xpansion_resource_tables

Revision ID: ebcae82af0c3
Revises: 3a7f9c2d1e8b
Create Date: 2026-03-18 10:42:12.608530

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ebcae82af0c3"
down_revision = "3a7f9c2d1e8b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "xpansion_constraint",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["xpansion_settings.study_id"],
            name=op.f("fk_xpansion_constraint_settings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "filename", name=op.f("pk_xpansion_constraint")),
    )

    op.create_table(
        "xpansion_capacity",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("matrix_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["xpansion_settings.study_id"],
            name=op.f("fk_xpansion_capacity_settings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "filename", name=op.f("pk_xpansion_capacity")),
    )

    op.create_table(
        "xpansion_weight",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("matrix_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["xpansion_settings.study_id"],
            name=op.f("fk_xpansion_weight_settings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "filename", name=op.f("pk_xpansion_weight")),
    )


def downgrade() -> None:
    op.drop_table("xpansion_weight")
    op.drop_table("xpansion_capacity")
    op.drop_table("xpansion_constraint")
