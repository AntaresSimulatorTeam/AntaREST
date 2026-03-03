"""create output metadata

Revision ID: f9ecc0607cc5
Revises: 9770c0960334
Create Date: 2025-12-24 10:27:58.254977

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f9ecc0607cc5"
down_revision = "562d4e1bd95d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "output_metadata",
        sa.Column("study_id", sa.String(), nullable=False, primary_key=True),
        sa.Column("output_name", sa.String(), nullable=False, primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
    )


def downgrade():
    op.drop_table("output_metadata")
