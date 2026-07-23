"""add_launchers_cache_table

Revision ID: ca04b7ebce70
Revises: 665f7b1d7575
Create Date: 2026-07-20 10:34:04.421275

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'ca04b7ebce70'
down_revision = '665f7b1d7575'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "launchers_cache",
        sa.Column("launcher_name", sa.String(20), nullable=False),
        sa.Column("allocated_cpu_rate", sa.Float(), nullable=False),
        sa.Column("cluster_load_rate", sa.Float(), nullable=False),
        sa.Column("nb_queued_jobs", sa.Integer(), nullable=False),
        sa.Column("launcher_status", sa.String(100), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("launcher_name", name="pk_launchers_cache"),
    )


def downgrade():
    op.drop_table("launchers_cache")
