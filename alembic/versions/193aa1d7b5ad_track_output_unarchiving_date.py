"""Track the last output unarchiving date.

Revision ID: 193aa1d7b5ad
Revises: 4b74045877f5
Create Date: 2026-10-21 10:22:29.967599

"""

import sqlalchemy as sa

from alembic import op

revision = "193aa1d7b5ad"
down_revision = "4b74045877f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column("last_unarchiving_date", sa.DateTime(), nullable=True))
        batch_op.alter_column("disk_space_bytes", existing_type=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    # Drop cache entries with unknown sizes before restoring the NOT NULL constraint.
    op.execute("DELETE FROM output WHERE disk_space_bytes IS NULL")

    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column("last_unarchiving_date")
        batch_op.alter_column("disk_space_bytes", existing_type=sa.BigInteger(), nullable=False)
