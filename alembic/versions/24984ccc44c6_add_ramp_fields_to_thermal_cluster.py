"""add_ramp_fields_to_thermal_cluster

Revision ID: 24984ccc44c6
Revises: e12d85a77641
Create Date: 2026-09-22 09:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "24984ccc44c6"
down_revision = "e12d85a77641"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("thermal_cluster") as batch_op:
        batch_op.add_column(sa.Column("ramp", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("max_ramp_up", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("max_ramp_down", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("ramp_up_cost", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("ramp_down_cost", sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table("thermal_cluster") as batch_op:
        batch_op.drop_column("ramp_down_cost")
        batch_op.drop_column("ramp_up_cost")
        batch_op.drop_column("max_ramp_down")
        batch_op.drop_column("max_ramp_up")
        batch_op.drop_column("ramp")
