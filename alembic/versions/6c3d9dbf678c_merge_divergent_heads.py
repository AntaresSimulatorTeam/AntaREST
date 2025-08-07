"""resolves a divergence in the Alembic migration history by merging multiple head revisions

Revision ID: 6c3d9dbf678c
Revises: fa59340767b0, a8c6e9d47b12
Create Date: 2025-07-28 11:07:02.181937

"""

# revision identifiers, used by Alembic.
revision = "6c3d9dbf678c"
down_revision = ("fa59340767b0", "a8c6e9d47b12")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
