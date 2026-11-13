"""add_needs_rescan_to_study_disk_space

Revision ID: c4d7a91e2b36
Revises: b8e5c1a7d902
Create Date: 2026-11-13 09:45:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c4d7a91e2b36"
down_revision = "b8e5c1a7d902"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("study_disk_space_analysis") as batch_op:
        batch_op.add_column(sa.Column("needs_rescan", sa.Boolean(), nullable=False, server_default=sa.false()))

    # Existing analyses may be outdated (e.g. outputs deleted since the last analysis): force a new analysis.
    analysis = sa.table("study_disk_space_analysis", sa.column("needs_rescan", sa.Boolean))
    op.execute(analysis.update().values(needs_rescan=True))


def downgrade() -> None:
    with op.batch_alter_table("study_disk_space_analysis") as batch_op:
        batch_op.drop_column("needs_rescan")
