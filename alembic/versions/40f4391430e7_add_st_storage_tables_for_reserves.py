"""add_st_storage_tables_for_reserves

Revision ID: 40f4391430e7
Revises: 6012b0407e38
Create Date: 2026-08-11 15:49:32.314554

"""

from sqlalchemy import Column, Float, ForeignKeyConstraint, String

from alembic import op

# revision identifiers, used by Alembic.
revision = '40f4391430e7'
down_revision = '6012b0407e38'
branch_labels = None
depends_on = None


def upgrade():
    # Certifications
    op.create_table(
        "st_storage_reserve_certifications",
        Column("study_id", String(36), nullable=False, primary_key=True),
        Column("area_id", String(255), nullable=False, primary_key=True),
        Column("st_storage_id", String(255), nullable=False, primary_key=True),
        Column("reserve_id", String(255), nullable=False, primary_key=True),
        Column("participation_cost", Float, nullable=False),
        Column("max_release", Float, nullable=False),
        Column("max_store", Float, nullable=False),
        ForeignKeyConstraint(
            ["study_id", "area_id", "st_storage_id"],
            ["st_storage.study_id", "st_storage.area_id", "st_storage.st_storage_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["study_id", "area_id", "reserve_id"],
            ["reserve_definition.study_id", "reserve_definition.area_id", "reserve_definition.reserve_id"],
            ondelete="CASCADE",
        ),
    )

    # Symmetries
    op.create_table(
        "st_storage_reserve_symmetries",
        Column("study_id", String(36), nullable=False, primary_key=True),
        Column("area_id", String(255), nullable=False, primary_key=True),
        Column("st_storage_id", String(255), nullable=False, primary_key=True),
        Column("symmetries", String(), nullable=False),
        ForeignKeyConstraint(
            ["study_id", "area_id", "st_storage_id"],
            ["st_storage.study_id", "st_storage.area_id", "st_storage.st_storage_id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("st_storage_reserve_certifications")
    op.drop_table("st_storage_reserve_symmetries")