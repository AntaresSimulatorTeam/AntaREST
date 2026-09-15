"""create_gems_library_tables

Revision ID: 0974bca4078d
Revises: c7e21b9f4a83
Create Date: 2026-09-15 11:44:27.559468

"""
from alembic import op
from sqlalchemy import String, Column, ForeignKeyConstraint, Boolean

from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = '0974bca4078d'
down_revision = 'c7e21b9f4a83'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gems_library_metadata",
        study_data_id_col(),
        Column("id", String(255), nullable=False),
        Column("description", String(), nullable=True),
        Column("version", String(36), nullable=True),
        ForeignKeyConstraint(["study_data_id"],["study_data.study_data_id"], ondelete="CASCADE"),
    )

    op.create_table(
        "gems_port_types",
        study_data_id_col(),
        Column("id", String(255), primary_key=True),
        Column("description", String(), nullable=True),
        Column("fields", String(), nullable=False),
        ForeignKeyConstraint(["study_data_id"], ["gems_library_metadata.study_data_id"], ondelete="CASCADE"),
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
        ForeignKeyConstraint(["study_data_id"], ["gems_library_metadata.study_data_id"], ondelete="CASCADE"),
    )

    op.create_table(
        "gems_models_ports",
        study_data_id_col(),
        Column("model_id", String(255), primary_key=True),
        Column("port_id", String(255), primary_key=True),
        Column("type", String(), nullable=False),
        ForeignKeyConstraint(["study_data_id", "model_id"],
            ["gems_models.study_data_id", "gems_models.id"],
            ondelete="CASCADE"
        ),
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
            ondelete="CASCADE"
        ),
    )

def downgrade():
    op.drop_table("gems_library_metadata")
    op.drop_table("gems_port_types")
    op.drop_table("gems_models")
    op.drop_table("gems_models_ports")
    op.drop_table("gems_models_parameters")
