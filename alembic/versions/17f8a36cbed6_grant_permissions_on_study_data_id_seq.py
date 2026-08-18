"""grant permissions on study_data_id_seq

Revision ID: 17f8a36cbed6
Revises: 1f0c9b2e7a34
Create Date: 2026-08-18 16:09:22.062707

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "17f8a36cbed6"
down_revision = "1f0c9b2e7a34"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == "sqlite":
        return

    # Previously created sequence does not have, by default, usage access for schema users
    # We need to grant it explicitly to avoid "insufficient privileges" errors
    op.execute(sa.text("GRANT USAGE, SELECT ON SEQUENCE study_data_study_data_id_seq TO public;"))


def downgrade():
    pass
