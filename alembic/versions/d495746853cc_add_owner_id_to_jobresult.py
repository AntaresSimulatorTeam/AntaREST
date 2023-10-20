"""Add owner_id to JobResult

Revision ID: d495746853cc
Revises: e65e0c04606b
Create Date: 2023-10-19 13:16:29.969047

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d495746853cc"
down_revision = "e65e0c04606b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), default=None))
        batch_op.create_foreign_key("fk_job_result_owner_id", "identities", ["owner_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("job_result", schema=None) as batch_op:
        batch_op.drop_column("owner_id")
