"""add_filters_to_districts

Revision ID: ae201048f056
Revises: bb26e0cd63ea
Create Date: 2026-10-05 10:29:38.881451

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae201048f056'
down_revision = 'bb26e0cd63ea'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("district") as batch_op:
        batch_op.add_column(sa.Column("filter_synthesis", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("filter_year_by_year", sa.String(), nullable=True))

def downgrade():
    with op.batch_alter_table("district") as batch_op:
        batch_op.drop_column("filter_synthesis")
        batch_op.drop_column("filter_year_by_year")