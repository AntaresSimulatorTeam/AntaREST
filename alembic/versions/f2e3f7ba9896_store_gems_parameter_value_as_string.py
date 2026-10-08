"""store_gems_parameter_value_as_string

Revision ID: f2e3f7ba9896
Revises: 3b48d03db4ef
Create Date: 2026-10-08 16:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f2e3f7ba9896"
down_revision = "3b48d03db4ef"
branch_labels = None
depends_on = None


def upgrade():
    # `value` now stores either a fixed numeric value or the `id` of a data series (e.g.
    # "demand_profile") as text, since a GEMS parameter can be assigned either kind of value.
    with op.batch_alter_table("gems_component_parameters", schema=None) as batch_op:
        batch_op.alter_column(
            "value",
            existing_type=sa.Float(),
            type_=sa.String(length=255),
            existing_nullable=False,
            postgresql_using="value::varchar(255)",
        )


def downgrade():
    with op.batch_alter_table("gems_component_parameters", schema=None) as batch_op:
        batch_op.alter_column(
            "value",
            existing_type=sa.String(length=255),
            type_=sa.Float(),
            existing_nullable=False,
            postgresql_using="value::double precision",
        )
