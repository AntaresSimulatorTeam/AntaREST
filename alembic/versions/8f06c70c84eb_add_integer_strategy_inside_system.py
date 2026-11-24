"""add_integer_strategy_inside_system

Revision ID: 8f06c70c84eb
Revises: 812d802c2d2d
Create Date: 2026-11-09 11:50:33.690220

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f06c70c84eb'
down_revision = '812d802c2d2d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.add_column(sa.Column("integer_strategy", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("gems_components") as batch_op:
        batch_op.drop_column("integer_strategy")

