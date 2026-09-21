"""add_thermal_cluster_ramping_to_optimization_preferences

Revision ID: e12d85a77641
Revises: e6892cbcad66
Create Date: 2026-09-17 10:28:26.615150

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e12d85a77641"
down_revision = "e6892cbcad66"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("optimization_preferences") as batch_op:
        batch_op.add_column(sa.Column("include_thermal_cluster_ramping", sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table("optimization_preferences") as batch_op:
        batch_op.drop_column("include_thermal_cluster_ramping")
