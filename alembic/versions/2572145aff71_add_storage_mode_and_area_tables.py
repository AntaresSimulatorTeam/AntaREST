"""add_storage_mode_and_area_tables

Revision ID: 2572145aff71
Revises: 9770c0960334
Create Date: 2025-01-17 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2572145aff71"
down_revision = "9770c0960334"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add storage_mode column to study table
    storagemode_enum = sa.Enum("FILESYSTEM", "DATABASE", name="storagemode")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        storagemode_enum.create(bind, checkfirst=True)

    op.add_column(
        "study",
        sa.Column(
            "storage_mode",
            storagemode_enum,
            nullable=False,
            server_default="FILESYSTEM",
        ),
    )
    op.create_index(op.f("ix_study_storage_mode"), "study", ["storage_mode"])

    # 2. Create area table
    op.create_table(
        "area",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("area_name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_area_study_id_study"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f("pk_area")),
    )

    # 3. Create area_ui table
    op.create_table(
        "area_ui",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("layer_id", sa.String(length=10), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.Column("color_r", sa.Integer(), nullable=False),
        sa.Column("color_g", sa.Integer(), nullable=False),
        sa.Column("color_b", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_area_ui_study_id_area_id_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "layer_id", name=op.f("pk_area_ui")),
    )


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
