"""change_reserves_format

Revision ID: 4121d3b48393
Revises: rp986cf862cy
Create Date: 2026-05-21 10:36:43.512270

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4121d3b48393'
down_revision = 'rp986cf862cy'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("compatibility_parameters") as batch_op:
        batch_op.drop_column("reserves_enabled")

    with op.batch_alter_table("optimization_preferences") as batch_op:
        batch_op.add_column(sa.Column("include_reserves", sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table("compatibility_parameters") as batch_op:
        batch_op.add_column(sa.Column("reserves_enabled", sa.Boolean(), nullable=True))

    with op.batch_alter_table("optimization_preferences") as batch_op:
        batch_op.drop_column("include_reserves")
