"""add_favorite_external_directory_table

Revision ID: 80fdf2408ede
Revises: rp986cf862cy
Create Date: 2026-06-10 13:33:16.721647

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80fdf2408ede'
down_revision = 'f50e7ed59478'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('favorite_external_directory',
                sa.Column('workspace', sa.String(length=255), nullable=False),
                sa.Column('path', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
                sa.ForeignKeyConstraint(['user_id'], ['identities.id'], ),
                sa.PrimaryKeyConstraint('workspace', 'path', 'user_id')
    )


def downgrade():
    op.drop_table('favorite_external_directory')
