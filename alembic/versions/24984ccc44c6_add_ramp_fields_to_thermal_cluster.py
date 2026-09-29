"""add_ramp_fields_to_thermal_cluster

Revision ID: 24984ccc44c6
Revises: 421f6d91d1f6
Create Date: 2026-09-22 09:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "24984ccc44c6"
down_revision = "421f6d91d1f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("thermal_cluster") as batch_op:
        batch_op.add_column(sa.Column("ramping_enabled", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("max_upward_power_ramping_rate", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("max_downward_power_ramping_rate", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("power_increase_cost", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("power_decrease_cost", sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table("thermal_cluster") as batch_op:
        batch_op.drop_column("power_decrease_cost")
        batch_op.drop_column("power_increase_cost")
        batch_op.drop_column("max_downward_power_ramping_rate")
        batch_op.drop_column("max_upward_power_ramping_rate")
        batch_op.drop_column("ramping_enabled")
