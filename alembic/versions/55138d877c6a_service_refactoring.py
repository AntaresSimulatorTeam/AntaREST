"""service_refactoring

Revision ID: 55138d877c6a
Revises: c83b8bb38a7c
Create Date: 2021-09-15 19:56:51.554898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55138d877c6a'
down_revision = 'c83b8bb38a7c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('variant_study_snapshot', schema=None) as batch_op:
        batch_op.drop_column('path')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('variant_study_snapshot', schema=None) as batch_op:
        batch_op.add_column(sa.Column('path', sa.VARCHAR(length=255), nullable=True))

    # ### end Alembic commands ###
