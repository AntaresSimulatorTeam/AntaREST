"""create_gems_components_connections_table

Revision ID: 3b48d03db4ef
Revises: ae201048f056
Create Date: 2026-09-29 15:53:54.445046

"""

from sqlalchemy import CheckConstraint, Column, ForeignKeyConstraint, PrimaryKeyConstraint, String, text

from alembic import op
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "3b48d03db4ef"
down_revision = "ae201048f056"
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
            [
                "gems_components.study_data_id",
                "gems_components.component_id",
            ],
            name="fk_gems_component_connections_component1_exists",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["study_data_id", "component2"],
            [
                "gems_components.study_data_id",
                "gems_components.component_id",
            ],
            name="fk_gems_component_connections_component2_exists",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "component1 != component2 or port1 != port2",
            name="ck_gems_component_connections_have_distinct_endpoints",
        ),
    )

    op.create_index(
        "uq_no_inverted_pairs",
        "gems_component_connections",
        [
            # `least`/`greatest` are not portable: SQLite has no such functions (and SQLite's
            # multi-argument `min`/`max` equivalents are not valid in PostgreSQL, which only has
            # aggregate `MIN`/`MAX`). `CASE` is standard SQL and works identically on both backends,
            # which matters since this migration also runs against SQLite in desktop mode.
            # The extra parentheses are required by PostgreSQL, which rejects a bare `CASE` expression
            # as an index key (unlike SQLite).
            text("(CASE WHEN component1 <= component2 THEN component1 ELSE component2 END)"),
            text("(CASE WHEN component1 >= component2 THEN component1 ELSE component2 END)"),
            text("(CASE WHEN port1 <= port2 THEN port1 ELSE port2 END)"),
            text("(CASE WHEN port1 >= port2 THEN port1 ELSE port2 END)"),
        ],
        unique=True,
    )


def downgrade():
    op.drop_table("gems_component_connections")
    op.drop_index("uq_no_inverted_pairs", table_name="gems_component_connections")
