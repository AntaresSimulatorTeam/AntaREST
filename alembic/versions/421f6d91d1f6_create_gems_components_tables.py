"""create_gems_components_tables

Revision ID: 421f6d91d1f6
Revises: e12d85a77641
Create Date: 2026-09-21 10:56:39.862102

"""

from sqlalchemy import Boolean, Column, Float, ForeignKeyConstraint, String

from alembic import op
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "421f6d91d1f6"
down_revision = "e12d85a77641"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gems_system_metadata",
        study_data_id_col(),
        Column("system_id", String(255), nullable=False),
        Column("description", String(255)),
        ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
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
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["study_data_id", "model_id"],
            ["gems_models.study_data_id", "gems_models.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["study_data_id", "scenario_group"],
            ["gems_scenario_builder.study_data_id", "gems_scenario_builder.scenario_group"],
            ondelete="CASCADE",
        ),
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
            ondelete="CASCADE",
        ),
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
            ondelete="CASCADE",
        ),
    )


def downgrade():
    op.drop_table("gems_component_properties")
    op.drop_table("gems_component_parameters")
    op.drop_table("gems_components")
    op.drop_table("gems_system_metadata")
