"""add_launchers_loads_table

Revision ID: d84134f661a9
Revises: e56b1130bc1f
Create Date: 2026-07-24 09:58:45.722848

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'd84134f661a9'
down_revision = 'e56b1130bc1f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "launchers_loads",
        sa.Column("launcher_name", sa.String(20), nullable=False),
        sa.Column("allocated_cpu_rate", sa.Float(), nullable=False),
        sa.Column("cluster_load_rate", sa.Float(), nullable=False),
        sa.Column("nb_queued_jobs", sa.Integer(), nullable=False),
        sa.Column("launcher_status", sa.String(100), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("launcher_name", name="pk_launchers_loads"),
    )


def downgrade():
    op.drop_table("launchers_loads")
