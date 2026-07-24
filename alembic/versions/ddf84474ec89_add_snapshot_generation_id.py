"""add snapshot generation ID

Revision ID: ddf84474ec89
Revises: d53f532e9b78
Create Date: 2026-07-24 14:12:37.276111

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ddf84474ec89"
down_revision = "d53f532e9b78"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("variant_study_snapshot", schema=None) as batch_op:
        batch_op.add_column(sa.Column("generation_id", sa.String(length=36), nullable=True))


def downgrade():
    with op.batch_alter_table("variant_study_snapshot", schema=None) as batch_op:
        batch_op.drop_column("generation_id")
