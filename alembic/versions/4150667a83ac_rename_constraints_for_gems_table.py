"""rename_constraints_for_gems_table

Revision ID: 4150667a83ac
Revises: 421f6d91d1f6
Create Date: 2026-09-29 10:39:23.209421

"""
from alembic import op
from sqlalchemy import Column, String, ForeignKeyConstraint, Boolean, PrimaryKeyConstraint, Float

from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = '4150667a83ac'
down_revision = '421f6d91d1f6'
branch_labels = None
depends_on = None


"""
Currently, lots of PKs and FKs on GEMS tables do not have any name.
So modifying / removing them is really complicated.
To solve this issue, this migration aims at giving names for all PKs and FKs on GEMS tables
This way, when we will want to change them in future works it will be easy.
"""

def upgrade():
    # First, drop all GEMS related tables in order to avoid FK issues
    op.drop_table("gems_component_properties")
    op.drop_table("gems_component_parameters")
    op.drop_table("gems_components")
    op.drop_table("gems_system_metadata")

    op.drop_table("gems_models_ports")
    op.drop_table("gems_models_parameters")
    op.drop_table("gems_models")
    op.drop_table("gems_port_types")
    op.drop_table("gems_library_metadata")

    op.drop_table("gems_taxonomy_categories")
    op.drop_table("gems_taxonomy_metadata")

    op.drop_table("gems_scenario_builder")

    # Then, recreate them and add names to the PKs and FKs.
    op.create_table(
        "gems_scenario_builder",
        study_data_id_col(),
        Column("scenario_group", String(255), primary_key=True),
        Column("data", String(), nullable=False),
        ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], name="fk_gems_scenario_builder", ondelete="CASCADE"),
        PrimaryKeyConstraint("study_data_id", "scenario_group", name="pk_gems_scenario_builder"),
    )

    op.create_table(
        "gems_taxonomy_metadata",
        study_data_id_col(),
        Column("id", String(255), nullable=False),
        Column("description", String(), nullable=True),
        ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], name="fk_gems_taxonomy_metadata", ondelete="CASCADE"),
        PrimaryKeyConstraint("study_data_id", name="pk_gems_taxonomy_metadata"),
    )

    op.create_table(
        "gems_taxonomy_categories",
        study_data_id_col(),
        Column("id", String(255), primary_key=True),
        Column("parent_category", String(255), nullable=True),
        Column("variables", String(), nullable=True),
        Column("parameters", String(), nullable=True),
        Column("ports", String(), nullable=True),
        Column("extra_outputs", String(), nullable=True),
        Column("properties", String(), nullable=True),
        Column("binding_constraints", String(), nullable=True),
        ForeignKeyConstraint(
            ["study_data_id", "parent_category"],
            ["gems_taxonomy_categories.study_data_id", "gems_taxonomy_categories.id"],
            name="fk_taxonomy_parent_category",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(["study_data_id"], ["gems_taxonomy_metadata.study_data_id"], name="fk_taxonomy_category_study_data", ondelete="CASCADE"),
        PrimaryKeyConstraint("study_data_id", "id", name="pk_gems_taxonomy_categories"),
    )

    op.create_table(
        "gems_library_metadata",
        study_data_id_col(),
        Column("id", String(255), nullable=False),
        Column("description", String(), nullable=True),
        Column("version", String(36), nullable=True),
        ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], name="fk_gems_library_metadata", ondelete="CASCADE"),
        PrimaryKeyConstraint("study_data_id", name="pk_gems_library_metadata"),
    )

    op.create_table(
        "gems_port_types",
        study_data_id_col(),
        Column("id", String(255), primary_key=True),
        Column("description", String(), nullable=True),
        Column("fields", String(), nullable=False),
        Column("area_connection", String(), nullable=True),
        Column("thermal_capacity_connection", String(), nullable=True),
        ForeignKeyConstraint(["study_data_id"], ["gems_library_metadata.study_data_id"], name="fk_gems_port_types", ondelete="CASCADE"),
        PrimaryKeyConstraint("study_data_id", "id", name="pk_gems_port_types"),
    )

    op.create_table(
        "gems_models",
        study_data_id_col(),
        Column("id", String(255), primary_key=True),
        Column("description", String(), nullable=True),
        Column("taxonomy_category", String(), nullable=True),
        Column("properties", String(), nullable=True),
        Column("variables", String(), nullable=False),
        Column("binding_constraints", String(), nullable=False),
        Column("constraints", String(), nullable=False),
        Column("objective_contributions", String(), nullable=False),
        Column("extra_outputs", String(), nullable=False),
        Column("port_field_definitions", String(), nullable=False),
        ForeignKeyConstraint(
            ["study_data_id"],
            ["gems_library_metadata.study_data_id"],
            name="fk_gems_models_library",
            ondelete="CASCADE"),
        ForeignKeyConstraint(
            ["study_data_id", "taxonomy_category"],
            ["gems_taxonomy_categories.study_data_id", "gems_taxonomy_categories.id"],
            name="fk_gems_models_taxonomy",
            ondelete="CASCADE"),
        PrimaryKeyConstraint("study_data_id", "id", name="pk_gems_models"),

    )

    op.create_table(
        "gems_models_ports",
        study_data_id_col(),
        Column("model_id", String(255), primary_key=True),
        Column("port_id", String(255), primary_key=True),
        Column("type", String(), nullable=False),
        ForeignKeyConstraint(["study_data_id", "model_id"],
                             ["gems_models.study_data_id", "gems_models.id"],
                             ondelete="CASCADE",
                             name="fk_gems_models_ports"
                             ),
        PrimaryKeyConstraint("study_data_id", "model_id", "port_id", name="pk_gems_models_ports"),
    )

    op.create_table(
        "gems_models_parameters",
        study_data_id_col(),
        Column("model_id", String(255), primary_key=True),
        Column("parameter_id", String(255), primary_key=True),
        Column("time_dependent", Boolean(), nullable=False),
        Column("scenario_dependent", Boolean(), nullable=False),
        ForeignKeyConstraint(["study_data_id", "model_id"],
                             ["gems_models.study_data_id", "gems_models.id"],
                             ondelete="CASCADE",
                             name="fk_gems_models_parameters"
                             ),
        PrimaryKeyConstraint("study_data_id", "model_id", "parameter_id", name="pk_gems_models_parameters"),
    )

    op.create_table(
        "gems_system_metadata",
        study_data_id_col(),
        Column("system_id", String(255), nullable=False),
        Column("description", String(255)),
        ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], name="fk_gems_system_metadata", ondelete="CASCADE"),
        PrimaryKeyConstraint("study_data_id", name="pk_gems_system_metadata"),
    )

    op.create_table(
        "gems_components",
        study_data_id_col(),
        Column("component_id", String(255), primary_key=True),
        Column("model_id", String(255)),
        Column("scenario_group", String(255), nullable=True),
        ForeignKeyConstraint(
            ["study_data_id"],
            ["gems_system_metadata.study_data_id"],
            name="fk_gems_components_to_system_metadata",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["study_data_id", "model_id"],
            ["gems_models.study_data_id", "gems_models.id"],
            name="fk_gems_components_to_models",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["study_data_id", "scenario_group"],
            ["gems_scenario_builder.study_data_id", "gems_scenario_builder.scenario_group"],
            name="fk_gems_components_to_scenario_group",
            ondelete="SET NULL",
        ),
        PrimaryKeyConstraint("study_data_id", "component_id", name="pk_gems_components"),
    )

    op.create_table(
        "gems_component_parameters",
        study_data_id_col(),
        Column("component_id", String(255), primary_key=True),
        Column("parameter_id", String(255), primary_key=True),
        Column("time_dependent", Boolean, nullable=False),
        Column("scenario_dependent", Boolean, nullable=False),
        Column("value", Float, nullable=False),
        ForeignKeyConstraint(
            ["study_data_id", "component_id"],
            ["gems_components.study_data_id", "gems_components.component_id"],
            name="fk_gems_component_parameters",
            ondelete="CASCADE",
        ),
        PrimaryKeyConstraint("study_data_id", "component_id", "parameter_id", name="pk_gems_component_parameters"),
    )

    op.create_table(
        "gems_component_properties",
        study_data_id_col(),
        Column("component_id", String(255), primary_key=True),
        Column("property_id", String(255), primary_key=True),
        Column("value", String(255), nullable=False),
        ForeignKeyConstraint(
            ["study_data_id", "component_id"],
            ["gems_components.study_data_id", "gems_components.component_id"],
            name="fk_gems_component_properties",
            ondelete="CASCADE",
        ),
        PrimaryKeyConstraint("study_data_id", "component_id", "property_id", name="pk_gems_component_properties"),

    )


def downgrade():
    # As we simply added names to PKs and FKs, there is nothing to do in the downgrade
    pass
