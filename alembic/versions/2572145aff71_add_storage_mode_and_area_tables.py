"""add_storage_mode_and_area_tables

Revision ID: 2572145aff71
Revises: d2942741ae68
Create Date: 2025-01-17 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2572145aff71"
down_revision = "d2942741ae68"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add storage_mode column to study table
    with op.batch_alter_table("study") as batch_op:
        batch_op.add_column(
            sa.Column(
                "storage_mode",
                sa.Enum("filesystem", "database", name="storagemode"),
                nullable=False,
                server_default="filesystem",
            )
        )
        batch_op.create_index(batch_op.f("ix_study_storage_mode"), ["storage_mode"], unique=False)

    # 2. Create area table
    op.create_table(
        "area",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("area_name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_area_study_id_study"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_area")),
        sa.UniqueConstraint("study_id", "area_id", name=op.f("uq_area_study_id_area_id")),
    )
    with op.batch_alter_table("area") as batch_op:
        batch_op.create_index(batch_op.f("ix_area_study_id"), ["study_id"], unique=False)

    # 3. Create area_ui table
    op.create_table(
        "area_ui",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.Column("layer_id", sa.String(length=10), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.Column("color_r", sa.Integer(), nullable=False),
        sa.Column("color_g", sa.Integer(), nullable=False),
        sa.Column("color_b", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["area.id"],
            name=op.f("fk_area_ui_area_id_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_area_ui")),
        sa.UniqueConstraint("area_id", "layer_id", name=op.f("uq_area_ui_area_id_layer_id")),
    )
    with op.batch_alter_table("area_ui") as batch_op:
        batch_op.create_index(batch_op.f("ix_area_ui_area_id"), ["area_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_area_ui_layer_id"), ["layer_id"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("area_ui")
    op.drop_table("area")

    # Drop storage_mode column and index
    with op.batch_alter_table("study") as batch_op:
        batch_op.drop_index(batch_op.f("ix_study_storage_mode"))
        batch_op.drop_column("storage_mode")

    # Drop enum type (PostgreSQL only)
    if op.get_context().dialect.name == "postgresql":
        sa.Enum(name="storagemode").drop(op.get_bind(), checkfirst=True)
