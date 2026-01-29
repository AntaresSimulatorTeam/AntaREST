"""add_foreign_key_users_favorite_table

Revision ID: 6a6d36e3c6ed
Revises: f3a153a9a048
Create Date: 2026-01-26 10:45:36.111886

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'y7x41d4a8yc'
down_revision = '7b406752d80'
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key("fk_user_id_favorite_study", "identities", "favorite_study", ["user_id"], ["id"], ondelete="CASCADE")


def downgrade():
    op.drop_constraint("fk_user_id_favorite_study", "identities", type_="foreignkey")
