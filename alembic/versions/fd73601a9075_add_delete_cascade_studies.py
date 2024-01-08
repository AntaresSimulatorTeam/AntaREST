"""
Add delete cascade constraint to study foreign keys

Revision ID: fd73601a9075
Revises: 3c70366b10ea
Create Date: 2024-02-12 17:27:37.314443
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "fd73601a9075"
down_revision = "3c70366b10ea"
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

    elif dialect_name == "sqlite":
        # Adding ondelete="CASCADE" to a foreign key in sqlite is not supported
        pass

    else:
        raise NotImplementedError(f"{dialect_name=} not implemented")


def downgrade() -> None:
    dialect_name: str = op.get_context().dialect.name
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

    elif dialect_name == "sqlite":
        # Removing ondelete="CASCADE" to a foreign key in sqlite is not supported
        pass

    else:
        raise NotImplementedError(f"{dialect_name=} not implemented")
