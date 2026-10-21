"""Initialize the output archiving reference date at deployment.

Revision ID: 6e24be113a72
Revises: 193aa1d7b5ad
Create Date: 2026-10-21

"""

from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision = "6e24be113a72"
down_revision = "193aa1d7b5ad"
branch_labels = None
depends_on = None

CONFIG_DATA = sa.table(
    "configdata",
    sa.column("owner", sa.Integer()),
    sa.column("key", sa.String()),
    sa.column("value", sa.String()),
)


def upgrade() -> None:
    op.execute(
        CONFIG_DATA.insert().values(
            owner=1,
            key="OUTPUT_ARCHIVING_REFERENCE_DATE",
            value=datetime.now(UTC).replace(tzinfo=None).isoformat(),
        )
    )


def downgrade() -> None:
    op.execute(
        CONFIG_DATA.delete().where(
            CONFIG_DATA.c.owner == 1,
            CONFIG_DATA.c.key.in_(["OUTPUT_ARCHIVING_REFERENCE_DATE", "OUTPUT_METADATA_INITIALIZED"]),
        )
    )
