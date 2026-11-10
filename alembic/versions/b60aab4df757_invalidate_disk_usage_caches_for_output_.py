"""invalidate disk usage caches for output archives

Revision ID: b60aab4df757
Revises: 3b48d03db4ef
Create Date: 2026-10-13 14:25:56.744479

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b60aab4df757"
down_revision = "3b48d03db4ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # These tables only cache sizes. Existing values omit output ZIP files
    # and must be rebuilt using the corrected disk usage calculation.
    op.execute(sa.table("output").delete())
    op.execute(sa.table("study_disk_space_analysis").delete())


def downgrade() -> None:
    # Cached sizes are regenerated on demand; there is no data to restore.
    pass
