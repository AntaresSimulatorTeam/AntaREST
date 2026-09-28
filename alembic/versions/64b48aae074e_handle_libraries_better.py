"""handle_libraries_better

Revision ID: 64b48aae074e
Revises: 421f6d91d1f6
Create Date: 2026-09-28 16:26:40.616785

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, Column

# revision identifiers, used by Alembic.
revision = '64b48aae074e'
down_revision = '421f6d91d1f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("gems_models", schema=None) as batch_op:
        batch_op.add_column(Column("library_id", String(255), primary_key=True))
        batch_op.create_foreign_key(
            "fk_gems_models_library_id",
            "gems_library_metadata",
            ["study_data_id", "library_id"],
            ["study_data_id", "id"],
            ondelete="CASCADE")

    with op.batch_alter_table("gems_components", schema=None) as batch_op:
        batch_op.add_column(Column("library_id", String(255)))
        # todo: modify the FK

def downgrade():
    with op.batch_alter_table("gems_models", schema=None) as batch_op:
        batch_op.drop_column("library_id")
        batch_op.drop_constraint("fk_gems_models_library_id", type_="foreignkey")

    with op.batch_alter_table("gems_components", schema=None) as batch_op:
        batch_op.drop_column("library_id")
        # todo: modify the FK back
