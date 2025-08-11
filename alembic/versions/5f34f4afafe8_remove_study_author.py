"""remove_study_author

Revision ID: 5f34f4afafe8
Revises: 6c3d9dbf678c
Create Date: 2025-08-11 15:19:59.580576

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "5f34f4afafe8"
down_revision = "6c3d9dbf678c"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("study", "author")


def downgrade():
    # Cannot restore content
    pass
