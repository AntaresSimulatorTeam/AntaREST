"""handle_multiple_gems_libraries

Revision ID: 20549c817795
Revises: 4150667a83ac
Create Date: 2026-09-29 13:00:29.725232

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20549c817795'
down_revision = '4150667a83ac'
branch_labels = None
depends_on = None


def upgrade():
    # Allow multiple libraries for a single study
    # To fit with this, specify the library of a component explicitly

    with op.batch_alter_table("gems_models") as batch_op:
        batch_op.add_column(sa.Column("library_id", sa.String(length=255), nullable=False))
        batch_op.drop_constraint("pk_gems_models", type_="primary")
        batch_op.create_primary_key("pk_gems_models", ["study_data_id", "library_id", "id"])

    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.add_column(sa.Column("library_id", sa.String(length=255), nullable=False))
        batch_op.drop_constraint("fk_gems_components_to_models", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_gems_components_to_models",
            "gems_models",
            ["study_data_id", "model_id", "library_id"],
            ["study_data_id", "id", "library_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("gems_library_metadata") as batch_op:
        batch_op.drop_constraint("pk_gems_library_metadata", type_="primary")
        batch_op.create_primary_key("pk_gems_library_metadata", ["study_data_id", "id"])

def downgrade():
    with op.batch_alter_table("gems_library_metadata") as batch_op:
        batch_op.drop_constraint("pk_gems_library_metadata", type_="primary")
        batch_op.create_primary_key("pk_gems_library_metadata", ["study_data_id"])

    with op.batch_alter_table("gems_models") as batch_op:
        batch_op.drop_constraint("pk_gems_models", type_="primary")
        batch_op.create_primary_key("pk_gems_models", ["study_data_id", "id"])
        batch_op.drop_column("library_id")

    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.drop_constraint("fk_gems_components_to_models", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_gems_components_to_models",
            "gems_models",
            ["study_data_id", "model_id"],
            ["study_data_id", "id"],
            ondelete="CASCADE",
        )
        batch_op.drop_column("library_id")
