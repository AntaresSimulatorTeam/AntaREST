"""Track output access and archive status.

Revision ID: 193aa1d7b5ad
Revises: b60aab4df757
Create Date: 2026-10-21 10:22:29.967599

"""

import sqlalchemy as sa

from alembic import op

revision = "193aa1d7b5ad"
down_revision = "b60aab4df757"
branch_labels = None
depends_on = None

OUTPUT = sa.table(
    "output",
    sa.column("disk_space_bytes", sa.BigInteger()),
)


def upgrade() -> None:
    with op.batch_alter_table("output") as batch_op:
        batch_op.add_column(sa.Column("last_access", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("archived", sa.Boolean(), nullable=True))
        batch_op.alter_column("disk_space_bytes", existing_type=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    # Drop cache entries with unknown sizes before restoring the NOT NULL constraint.
    op.execute(OUTPUT.delete().where(OUTPUT.c.disk_space_bytes.is_(None)))

    with op.batch_alter_table("output") as batch_op:
        batch_op.drop_column("archived")
        batch_op.drop_column("last_access")
        batch_op.alter_column("disk_space_bytes", existing_type=sa.BigInteger(), nullable=False)
