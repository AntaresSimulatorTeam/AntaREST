"""add_invalidated_at_to_study_disk_space

Revision ID: c4d7a91e2b36
Revises: 1c8b0b189035
Create Date: 2026-11-13 09:45:00.000000

"""

import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c4d7a91e2b36"
down_revision = "1c8b0b189035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("study_disk_space_analysis") as batch_op:
        batch_op.add_column(sa.Column("invalidated_at", sa.DateTime(), nullable=True))

    # Existing analyses may be outdated (e.g. outputs deleted since the last analysis): force a new analysis.
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    analysis = sa.table("study_disk_space_analysis", sa.column("invalidated_at", sa.DateTime))
    op.execute(analysis.update().values(invalidated_at=now))


def downgrade() -> None:
    with op.batch_alter_table("study_disk_space_analysis") as batch_op:
        batch_op.drop_column("invalidated_at")
