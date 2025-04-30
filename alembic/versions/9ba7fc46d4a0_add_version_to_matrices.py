"""add version to matrices

Revision ID: 9ba7fc46d4a0
Revises: 423fe2c8ee40
Create Date: 2025-04-09 09:46:00.086961

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ba7fc46d4a0'
down_revision = '423fe2c8ee40'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('matrix', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default="1"))


def downgrade():
    with op.batch_alter_table('matrix', schema=None) as batch_op:
        batch_op.drop_column('version')
