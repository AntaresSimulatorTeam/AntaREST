"""add_commandblock_index

Revision ID: 423fe2c8ee40
Revises: bae9c99bc42d
Create Date: 2025-02-27 14:08:50.413459

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "423fe2c8ee40"
down_revision = "bae9c99bc42d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("commandblock", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_commandblock_study_id"), ["study_id"], unique=False)


def downgrade():
    with op.batch_alter_table("commandblock", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_commandblock_study_id"))
