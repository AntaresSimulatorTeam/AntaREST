"""add_output_aggregation_table

Revision ID: d19bdf81aa45
Revises: 9ba7fc46d4a0
Create Date: 2025-05-07 11:16:12.317085

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d19bdf81aa45"
down_revision = "9ba7fc46d4a0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "output_aggregation",
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("taskjob.id", name="fk_oa_taskjob", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "download_id",
            sa.String(36),
            sa.ForeignKey("file_download.id", name="fk_oa_fd", ondelete="CASCADE"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("output_aggregation")
