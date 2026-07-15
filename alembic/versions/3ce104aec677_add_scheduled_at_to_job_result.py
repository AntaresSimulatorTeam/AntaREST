"""add scheduled_at to job_result

Revision ID: 3ce104aec677
Revises: 665f7b1d7575
Create Date: 2026-07-15 10:14:01.388332

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3ce104aec677"
down_revision = "665f7b1d7575"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.add_column(sa.Column("scheduled_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.drop_column("scheduled_at")
