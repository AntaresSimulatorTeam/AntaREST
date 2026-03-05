"""
Add celery_task_mapping table

This table stores the mapping between application TaskJob IDs and
Celery AsyncResult IDs. It is only used by the CeleryTaskService
implementation.

Revision ID: a1b2c3d4e5f6
Revises: 562d4e1bd95d
Create Date: 2026-03-05
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "562d4e1bd95d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "celery_task_mapping",
        sa.Column(
            "task_id",
            sa.String(),
            sa.ForeignKey("taskjob.id", name="fk_celery_mapping_taskjob_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("celery_id", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("celery_task_mapping")
