"""handle_multiple_gems_libraries

Revision ID: 20549c817795
Revises: 4150667a83ac
Create Date: 2026-09-29 13:00:29.725232

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20549c817795"
down_revision = "4150667a83ac"
branch_labels = None
depends_on = None


def upgrade():
    """
    Allow multiple libraries for a single study
    To fit with this, specify the library of a component explicitly
    """

    # Before dropping a Primary Key, drop the Foreign Keys linked to it
    with op.batch_alter_table("gems_models_ports") as batch_op:
        batch_op.drop_constraint("fk_gems_models_ports", type_="foreignkey")

    with op.batch_alter_table("gems_models_parameters") as batch_op:
        batch_op.drop_constraint("fk_gems_models_parameters", type_="foreignkey")

    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.drop_constraint("fk_gems_components_to_models", type_="foreignkey")

    # Modify the Primary Key now that is not referenced anywhere
    with op.batch_alter_table("gems_models") as batch_op:
        batch_op.add_column(sa.Column("library_id", sa.String(length=255), nullable=False))
        batch_op.drop_constraint("pk_gems_models", type_="primary")
        batch_op.create_primary_key("pk_gems_models", ["study_data_id", "library_id", "id"])

    # Add the `library_id` column and put back the dropped foreign keys.
    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.add_column(sa.Column("library_id", sa.String(length=255), nullable=False))
        batch_op.create_foreign_key(
            "fk_gems_components_to_models",
            "gems_models",
            ["study_data_id", "model_id", "library_id"],
            ["study_data_id", "id", "library_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("gems_models_ports") as batch_op:
        batch_op.add_column(sa.Column("library_id", sa.String(length=255), nullable=False))
        batch_op.create_foreign_key(
            "fk_gems_models_ports",
            "gems_models",
            ["study_data_id", "model_id", "library_id"],
            ["study_data_id", "id", "library_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("gems_models_parameters") as batch_op:
        batch_op.add_column(sa.Column("library_id", sa.String(length=255), nullable=False))
        batch_op.create_foreign_key(
            "fk_gems_models_parameters",
            "gems_models",
            ["study_data_id", "model_id", "library_id"],
            ["study_data_id", "id", "library_id"],
            ondelete="CASCADE",
        )

    # Before dropping a Primary Key, drop the Foreign Keys linked to it
    with op.batch_alter_table("gems_models") as batch_op:
        batch_op.drop_constraint("fk_gems_models_library", type_="foreignkey")

    with op.batch_alter_table("gems_port_types") as batch_op:
        batch_op.drop_constraint("fk_gems_port_types", type_="foreignkey")

    # Modify the Primary Key of the library metadata table to allow multiple libraries inside a study
    with op.batch_alter_table("gems_library_metadata") as batch_op:
        batch_op.drop_constraint("pk_gems_library_metadata", type_="primary")
        batch_op.create_primary_key("pk_gems_library_metadata", ["study_data_id", "id"])

    # Add the `library_id` column and put back the dropped Foreign Keys
    with op.batch_alter_table("gems_models") as batch_op:
        batch_op.create_foreign_key(
            "fk_gems_models_library",
            "gems_library_metadata",
            ["study_data_id", "library_id"],
            ["study_data_id", "id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("gems_port_types") as batch_op:
        batch_op.add_column(sa.Column("library_id", sa.String(length=255), nullable=False))
        batch_op.create_foreign_key(
            "fk_gems_port_types",
            "gems_library_metadata",
            ["study_data_id", "library_id"],
            ["study_data_id", "id"],
            ondelete="CASCADE",
        )


def downgrade():
    with op.batch_alter_table("gems_port_types") as batch_op:
        batch_op.drop_constraint("fk_gems_port_types", type_="foreignkey")
        batch_op.drop_column("library_id")

    with op.batch_alter_table("gems_models") as batch_op:
        batch_op.drop_constraint("fk_gems_models_library", type_="foreignkey")

    with op.batch_alter_table("gems_library_metadata") as batch_op:
        batch_op.drop_constraint("pk_gems_library_metadata", type_="primary")
        batch_op.create_primary_key("pk_gems_library_metadata", ["study_data_id"])

    with op.batch_alter_table("gems_models") as batch_op:
        batch_op.create_foreign_key(
            "fk_gems_models_library",
            "gems_library_metadata",
            ["study_data_id"],
            ["study_data_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("gems_port_types") as batch_op:
        batch_op.create_foreign_key(
            "fk_gems_port_types",
            "gems_library_metadata",
            ["study_data_id"],
            ["study_data_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("gems_models_parameters") as batch_op:
        batch_op.drop_constraint("fk_gems_models_parameters", type_="foreignkey")
        batch_op.drop_column("library_id")

    with op.batch_alter_table("gems_models_ports") as batch_op:
        batch_op.drop_constraint("fk_gems_models_ports", type_="foreignkey")
        batch_op.drop_column("library_id")

    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.drop_constraint("fk_gems_components_to_models", type_="foreignkey")
        batch_op.drop_column("library_id")

    with op.batch_alter_table("gems_models") as batch_op:
        batch_op.drop_constraint("pk_gems_models", type_="primary")
        batch_op.drop_column("library_id")
        batch_op.create_primary_key("pk_gems_models", ["study_data_id", "id"])

    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.create_foreign_key(
            "fk_gems_components_to_models",
            "gems_models",
            ["study_data_id", "model_id"],
            ["study_data_id", "id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("gems_models_parameters") as batch_op:
        batch_op.create_foreign_key(
            "fk_gems_models_parameters",
            "gems_models",
            ["study_data_id", "model_id"],
            ["study_data_id", "id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("gems_models_ports") as batch_op:
        batch_op.create_foreign_key(
            "fk_gems_models_ports",
            "gems_models",
            ["study_data_id", "model_id"],
            ["study_data_id", "id"],
            ondelete="CASCADE",
        )
