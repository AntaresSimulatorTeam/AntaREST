"""add_study_new_missing_field

Revision ID: ef72a8a1c9cf
Revises: 2a8c5e41f214
Create Date: 2022-03-10 08:00:30.537617

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef72a8a1c9cf'
down_revision = '2a8c5e41f214'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rawstudy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('missing', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rawstudy', schema=None) as batch_op:
        batch_op.drop_column('missing')

    # ### end Alembic commands ###
