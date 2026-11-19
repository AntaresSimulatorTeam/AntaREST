"""add_threshold_ens_to_adequacy_patch_parameters

Revision ID: 55ae4521e871
Revises: c4d7e9a1f3b2
Create Date: 2026-11-17 11:45:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "55ae4521e871"
down_revision = "c4d7e9a1f3b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("adequacy_patch_parameters") as batch_op:
        batch_op.add_column(sa.Column("threshold_ens", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("adequacy_patch_parameters") as batch_op:
        batch_op.drop_column("threshold_ens")
