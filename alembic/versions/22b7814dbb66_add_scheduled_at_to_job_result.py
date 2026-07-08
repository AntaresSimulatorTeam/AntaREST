"""add scheduled_at to job_result

Revision ID: 22b7814dbb66
Revises: 80fdf2408ede
Create Date: 2026-07-01 15:51:09.090025

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "22b7814dbb66"
down_revision = "80fdf2408ede"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.add_column(sa.Column("scheduled_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.drop_column("scheduled_at")
