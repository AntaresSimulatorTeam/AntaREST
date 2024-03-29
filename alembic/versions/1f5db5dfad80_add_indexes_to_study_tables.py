# noinspection SpellCheckingInspection
"""
Add indexes to Study tables

The goal of this migration is to add indexes on the `study`, `rawstudy` and `study_additional_data` tables,
in order to speed up data search queries for the search engine.

Revision ID: 1f5db5dfad80
Revises: 782a481f3414
Create Date: 2024-01-19 18:37:34.155199
"""
from alembic import op
import sqlalchemy as sa  # type: ignore


# revision identifiers, used by Alembic.
# noinspection SpellCheckingInspection
revision = "1f5db5dfad80"
down_revision = "782a481f3414"
branch_labels = None
depends_on = None


# noinspection SpellCheckingInspection
def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("rawstudy", schema=None) as batch_op:
        batch_op.alter_column("workspace", existing_type=sa.VARCHAR(length=255), nullable=False)
        batch_op.create_index(batch_op.f("ix_rawstudy_missing"), ["missing"], unique=False)
        batch_op.create_index(batch_op.f("ix_rawstudy_workspace"), ["workspace"], unique=False)

    with op.batch_alter_table("study", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_study_archived"), ["archived"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_folder"), ["folder"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_name"), ["name"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_owner_id"), ["owner_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_parent_id"), ["parent_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_type"), ["type"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_updated_at"), ["updated_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_version"), ["version"], unique=False)

    with op.batch_alter_table("study_additional_data", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_study_additional_data_patch"), ["patch"], unique=False)

    # ### end Alembic commands ###


# noinspection SpellCheckingInspection
def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("study_additional_data", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_study_additional_data_patch"))

    with op.batch_alter_table("study", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_study_version"))
        batch_op.drop_index(batch_op.f("ix_study_updated_at"))
        batch_op.drop_index(batch_op.f("ix_study_type"))
        batch_op.drop_index(batch_op.f("ix_study_parent_id"))
        batch_op.drop_index(batch_op.f("ix_study_owner_id"))
        batch_op.drop_index(batch_op.f("ix_study_name"))
        batch_op.drop_index(batch_op.f("ix_study_folder"))
        batch_op.drop_index(batch_op.f("ix_study_created_at"))
        batch_op.drop_index(batch_op.f("ix_study_archived"))

    with op.batch_alter_table("rawstudy", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_rawstudy_workspace"))
        batch_op.drop_index(batch_op.f("ix_rawstudy_missing"))
        batch_op.alter_column("workspace", existing_type=sa.VARCHAR(length=255), nullable=True)

    # ### end Alembic commands ###
