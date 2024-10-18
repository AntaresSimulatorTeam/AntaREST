"""add_task_progress

Revision ID: b33e1f57a60c
Revises: 490b80a84bb5
Create Date: 2024-10-17 14:17:50.774587

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b33e1f57a60c'
down_revision = '490b80a84bb5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('taskjob', schema=None) as batch_op:
        batch_op.add_column(sa.Column('progress', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('taskjob', schema=None) as batch_op:
        batch_op.drop_column('progress')
