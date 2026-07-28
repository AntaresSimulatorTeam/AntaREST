"""add_schedule_at_to_job_result

Revision ID: df6c6eb845b9
Revises: d84134f661a9
Create Date: 2026-07-28 15:30:51.790004

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "df6c6eb845b9"
down_revision = "d84134f661a9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.add_column(sa.Column("scheduled_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.drop_column("scheduled_at")
