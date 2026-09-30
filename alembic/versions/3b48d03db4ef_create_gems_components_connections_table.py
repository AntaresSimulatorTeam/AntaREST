"""create_gems_components_connections_table

Revision ID: 3b48d03db4ef
Revises: 24984ccc44c6
Create Date: 2026-09-29 15:53:54.445046

"""

from sqlalchemy import CheckConstraint, Column, ForeignKeyConstraint, PrimaryKeyConstraint, String

from alembic import op
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "3b48d03db4ef"
down_revision = "24984ccc44c6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gems_component_connections",
        study_data_id_col(),
        Column("component1", String(255), primary_key=True),
        Column("component2", String(255), primary_key=True),
        Column("port1", String(255), primary_key=True),
        Column("port2", String(255), primary_key=True),
        PrimaryKeyConstraint(
            "study_data_id", "component1", "component2", "port1", "port2", name="pk_gems_component_connections"
        ),
        ForeignKeyConstraint(
            ["study_data_id", "component1"],
            ["gems_components.study_data_id", "gems_components.component_id"],
            name="fk_gems_component_connections_component1",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["study_data_id", "component2"],
            ["gems_components.study_data_id", "gems_components.component_id"],
            name="fk_gems_component_connections_component2",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "component1 != component2",
            name="ck_gems_component_connections_component1_not_equals_component2",
        ),
    )


def downgrade():
    op.drop_table("gems_component_connections")
