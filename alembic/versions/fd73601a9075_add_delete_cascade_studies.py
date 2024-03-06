"""
Add delete cascade constraint to study foreign keys

Revision ID: fd73601a9075
Revises: 3c70366b10ea
Create Date: 2024-02-12 17:27:37.314443
"""
import sqlalchemy as sa  # type: ignore
from alembic import op

# revision identifiers, used by Alembic.
revision = "fd73601a9075"
down_revision = "dae93f1d9110"
branch_labels = None
depends_on = None

# noinspection SpellCheckingInspection
RAWSTUDY_FK = "rawstudy_id_fkey"

# noinspection SpellCheckingInspection
VARIANTSTUDY_FK = "variantstudy_id_fkey"

# noinspection SpellCheckingInspection
STUDY_ADDITIONAL_DATA_FK = "study_additional_data_study_id_fkey"


def upgrade() -> None:
    dialect_name: str = op.get_context().dialect.name

    # SQLite doesn't support dropping foreign keys, so we need to ignore it here
    if dialect_name == "postgresql":
        with op.batch_alter_table("rawstudy", schema=None) as batch_op:
            batch_op.drop_constraint(RAWSTUDY_FK, type_="foreignkey")
            batch_op.create_foreign_key(RAWSTUDY_FK, "study", ["id"], ["id"], ondelete="CASCADE")

        with op.batch_alter_table("study_additional_data", schema=None) as batch_op:
            batch_op.drop_constraint(STUDY_ADDITIONAL_DATA_FK, type_="foreignkey")
            batch_op.create_foreign_key(STUDY_ADDITIONAL_DATA_FK, "study", ["study_id"], ["id"], ondelete="CASCADE")

        with op.batch_alter_table("variantstudy", schema=None) as batch_op:
            batch_op.drop_constraint(VARIANTSTUDY_FK, type_="foreignkey")
            batch_op.create_foreign_key(VARIANTSTUDY_FK, "study", ["id"], ["id"], ondelete="CASCADE")

    with op.batch_alter_table("group_metadata", schema=None) as batch_op:
        batch_op.alter_column("group_id", existing_type=sa.VARCHAR(length=36), nullable=False)
        batch_op.alter_column("study_id", existing_type=sa.VARCHAR(length=36), nullable=False)
        batch_op.create_index(batch_op.f("ix_group_metadata_group_id"), ["group_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_group_metadata_study_id"), ["study_id"], unique=False)
        if dialect_name == "postgresql":
            batch_op.drop_constraint("group_metadata_group_id_fkey", type_="foreignkey")
            batch_op.drop_constraint("group_metadata_study_id_fkey", type_="foreignkey")
            batch_op.create_foreign_key(
                "group_metadata_group_id_fkey", "groups", ["group_id"], ["id"], ondelete="CASCADE"
            )
            batch_op.create_foreign_key(
                "group_metadata_study_id_fkey", "study", ["study_id"], ["id"], ondelete="CASCADE"
            )


def downgrade() -> None:
    dialect_name: str = op.get_context().dialect.name
    # SQLite doesn't support dropping foreign keys, so we need to ignore it here
    if dialect_name == "postgresql":
        with op.batch_alter_table("rawstudy", schema=None) as batch_op:
            batch_op.drop_constraint(RAWSTUDY_FK, type_="foreignkey")
            batch_op.create_foreign_key(RAWSTUDY_FK, "study", ["id"], ["id"])

        with op.batch_alter_table("study_additional_data", schema=None) as batch_op:
            batch_op.drop_constraint(STUDY_ADDITIONAL_DATA_FK, type_="foreignkey")
            batch_op.create_foreign_key(STUDY_ADDITIONAL_DATA_FK, "study", ["study_id"], ["id"])

        with op.batch_alter_table("variantstudy", schema=None) as batch_op:
            batch_op.drop_constraint(VARIANTSTUDY_FK, type_="foreignkey")
            batch_op.create_foreign_key(VARIANTSTUDY_FK, "study", ["id"], ["id"])

    with op.batch_alter_table("group_metadata", schema=None) as batch_op:
        # SQLite doesn't support dropping foreign keys, so we need to ignore it here
        if dialect_name == "postgresql":
            batch_op.drop_constraint("group_metadata_study_id_fkey", type_="foreignkey")
            batch_op.drop_constraint("group_metadata_group_id_fkey", type_="foreignkey")
            batch_op.create_foreign_key("group_metadata_study_id_fkey", "study", ["study_id"], ["id"])
            batch_op.create_foreign_key("group_metadata_group_id_fkey", "groups", ["group_id"], ["id"])
        batch_op.drop_index(batch_op.f("ix_group_metadata_study_id"))
        batch_op.drop_index(batch_op.f("ix_group_metadata_group_id"))
        batch_op.alter_column("study_id", existing_type=sa.VARCHAR(length=36), nullable=True)
        batch_op.alter_column("group_id", existing_type=sa.VARCHAR(length=36), nullable=True)
