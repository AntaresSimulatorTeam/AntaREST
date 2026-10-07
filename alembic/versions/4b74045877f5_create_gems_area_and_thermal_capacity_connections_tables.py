"""create_gems_area_and_thermal_capacity_connections_tables

Revision ID: 4b74045877f5
Revises: ae201048f056
Create Date: 2026-10-01 10:45:00.000000

"""

import sqlalchemy as sa

from alembic import op
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "4b74045877f5"
down_revision = "ae201048f056"
branch_labels = None
depends_on = None


def _component_model_foreign_key(table_name: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["study_data_id", "component_id", "library_id", "model_id"],
        [
            "gems_components.study_data_id",
            "gems_components.component_id",
            "gems_components.library_id",
            "gems_components.model_id",
        ],
        name=f"fk_{table_name}_component",
        ondelete="CASCADE",
    )


def _port_foreign_key(table_name: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["study_data_id", "library_id", "model_id", "port_id"],
        [
            "gems_models_ports.study_data_id",
            "gems_models_ports.library_id",
            "gems_models_ports.model_id",
            "gems_models_ports.port_id",
        ],
        name=f"fk_{table_name}_port",
        ondelete="CASCADE",
    )


def upgrade() -> None:
    # Allows connections tables to reference `(study_data_id, component_id, library_id, model_id)`
    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.create_unique_constraint(
            "uq_gems_components_component_library_model",
            ["study_data_id", "component_id", "library_id", "model_id"],
        )

    op.create_table(
        "gems_area_connections",
        study_data_id_col(primary_key=False),
        sa.Column("component_id", sa.String(length=255), nullable=False),
        sa.Column("port_id", sa.String(length=255), nullable=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        _component_model_foreign_key("gems_area_connections"),
        _port_foreign_key("gems_area_connections"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "area_id"],
            ["area.study_data_id", "area.area_id"],
            name="fk_gems_area_connections_area",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_data_id", "component_id", "port_id", name="pk_gems_area_connections"),
    )

    op.create_table(
        "gems_thermal_capacity_connections",
        study_data_id_col(primary_key=False),
        sa.Column("component_id", sa.String(length=255), nullable=False),
        sa.Column("port_id", sa.String(length=255), nullable=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("cluster_id", sa.String(length=255), nullable=False),
        _component_model_foreign_key("gems_thermal_capacity_connections"),
        _port_foreign_key("gems_thermal_capacity_connections"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "area_id", "cluster_id"],
            ["thermal_cluster.study_data_id", "thermal_cluster.area_id", "thermal_cluster.thermal_id"],
            name="fk_gems_thermal_capacity_connections_cluster",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "study_data_id", "component_id", "port_id", name="pk_gems_thermal_capacity_connections"
        ),
    )


def downgrade() -> None:
    op.drop_table("gems_thermal_capacity_connections")
    op.drop_table("gems_area_connections")

    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.drop_constraint("uq_gems_components_component_library_model", type_="unique")
