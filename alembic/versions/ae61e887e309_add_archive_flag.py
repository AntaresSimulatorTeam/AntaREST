"""add archive flag

Revision ID: ae61e887e309
Revises: 15f3bce09264
Create Date: 2021-08-03 10:04:45.500466

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae61e887e309'
down_revision = '15f3bce09264'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    default_boolean = sa.text('0') if op.get_context().dialect.name == 'sqlite' else 'f'
    with op.batch_alter_table('study', schema=None) as batch_op:
        batch_op.add_column(sa.Column('archived', sa.Boolean(), server_default=default_boolean, nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('study', schema=None) as batch_op:
        batch_op.drop_column('archived')

    # ### end Alembic commands ###
