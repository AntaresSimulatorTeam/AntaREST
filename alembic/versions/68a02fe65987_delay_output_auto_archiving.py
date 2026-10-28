"""start output auto archive deployment grace period

Revision ID: 68a02fe65987
Revises: 193aa1d7b5ad
Create Date: 2026-10-28 10:31:31.740555

"""

from datetime import datetime, timezone

import sqlalchemy as sa

from alembic import op

revision = "68a02fe65987"
down_revision = "193aa1d7b5ad"
branch_labels = None
depends_on = None

configdata = sa.table(
    "configdata",
    sa.column("owner", sa.Integer()),
    sa.column("key", sa.String()),
    sa.column("value", sa.String()),
)


def upgrade() -> None:
    # Protect pre-upgrade outputs for one retention period without inventing unarchiving dates.
    op.bulk_insert(
        configdata,
        [
            {
                "owner": 1,
                "key": "OUTPUT_AUTO_ARCHIVE_MIGRATION_DATE",
                "value": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        configdata.delete().where(configdata.c.owner == 1, configdata.c.key == "OUTPUT_AUTO_ARCHIVE_MIGRATION_DATE")
    )
