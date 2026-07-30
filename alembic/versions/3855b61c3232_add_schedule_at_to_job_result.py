"""add schedule_at to job_result

Revision ID: 3855b61c3232
Revises: cbf69219c1b6
Create Date: 2026-07-28 17:02:49.701163

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3855b61c3232"
down_revision = "cbf69219c1b6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.add_column(sa.Column("scheduled_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.drop_column("scheduled_at")
