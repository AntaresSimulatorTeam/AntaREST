"""Add owner_name to JobResult

Revision ID: d495746853cc
Revises: e65e0c04606b
Create Date: 2023-10-19 13:16:29.969047

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey


# revision identifiers, used by Alembic.
revision = 'd495746853cc'
down_revision = 'e65e0c04606b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('job_result', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_name', sa.String(), default="Unknown user"))
        batch_op.create_foreign_key('fk_job_result_owner_name', 'identities', ['owner_name'], ['name'])


def downgrade():
    with op.batch_alter_table('job_result', schema=None) as batch_op:
        batch_op.drop_column("owner_name")
