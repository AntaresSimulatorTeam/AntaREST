"""create_gems_components_connections_table

Revision ID: 3b48d03db4ef
Revises: bb26e0cd63ea
Create Date: 2026-09-29 15:53:54.445046

"""

from sqlalchemy import CheckConstraint, Column, ForeignKeyConstraint, PrimaryKeyConstraint, String

from alembic import op
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "3b48d03db4ef"
down_revision = "bb26e0cd63ea"
branch_labels = None
depends_on = None


def upgrade():
    # Add unique constraint so that `gems_component_connections` can reference `(study_data_id, component1/2,
    # library_id1/2, model_id1/2)`
    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.create_unique_constraint(
            "uq_gems_components_component_library_model",
            ["study_data_id", "component_id", "library_id", "model_id"],
        )

    op.create_table(
        "gems_component_connections",
        study_data_id_col(),
        Column("component1", String(255), primary_key=True),
        Column("component2", String(255), primary_key=True),
        Column("port1", String(255), primary_key=True),
        Column("port2", String(255), primary_key=True),
        Column("library_id1", String(255), nullable=False),
        Column("model_id1", String(255), nullable=False),
        Column("library_id2", String(255), nullable=False),
        Column("model_id2", String(255), nullable=False),
        PrimaryKeyConstraint(
            "study_data_id", "component1", "component2", "port1", "port2", name="pk_gems_component_connections"
        ),
        ForeignKeyConstraint(
            ["study_data_id", "component1", "library_id1", "model_id1"],
            [
                "gems_components.study_data_id",
                "gems_components.component_id",
                "gems_components.library_id",
                "gems_components.model_id",
            ],
            name="fk_gems_component_connections_component1_model",
            ondelete="CASCADE",
        ),
        # Ensures `port1` is actually a port of component1's model.
        ForeignKeyConstraint(
            ["study_data_id", "library_id1", "model_id1", "port1"],
            [
                "gems_models_ports.study_data_id",
                "gems_models_ports.library_id",
                "gems_models_ports.model_id",
                "gems_models_ports.port_id",
            ],
            name="fk_gems_component_connections_port1",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["study_data_id", "component2", "library_id2", "model_id2"],
            [
                "gems_components.study_data_id",
                "gems_components.component_id",
                "gems_components.library_id",
                "gems_components.model_id",
            ],
            name="fk_gems_component_connections_component2_model",
            ondelete="CASCADE",
        ),
        # Ensures `port2` is actually a port of component1's model.
        ForeignKeyConstraint(
            ["study_data_id", "library_id2", "model_id2", "port2"],
            [
                "gems_models_ports.study_data_id",
                "gems_models_ports.library_id",
                "gems_models_ports.model_id",
                "gems_models_ports.port_id",
            ],
            name="fk_gems_component_connections_port2",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "component1 != component2",
            name="ck_gems_component_connections_component1_not_equals_component2",
        ),
    )


def downgrade():
    op.drop_table("gems_component_connections")

    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.drop_constraint("uq_gems_components_component_library_model", type_="unique")

