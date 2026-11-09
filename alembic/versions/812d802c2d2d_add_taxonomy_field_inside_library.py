"""add_taxonomy_field_inside_library

Revision ID: 812d802c2d2d
Revises: f2e3f7ba9896
Create Date: 2026-11-09 11:04:51.652538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '812d802c2d2d'
down_revision = 'f2e3f7ba9896'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("gems_library_metadata") as batch_op:
        batch_op.add_column(sa.Column("taxonomy", sa.String(length=255), nullable=True))
        batch_op.create_foreign_key(
            "fk_gems_library_taxonomy",
            "gems_taxonomy_metadata",
            ["study_data_id", "taxonomy"],
            ["study_data_id", "id"],
            ondelete="CASCADE",
        )


def downgrade():
    with op.batch_alter_table("gems_library_metadata") as batch_op:
        batch_op.drop_constraint("fk_gems_library_taxonomy", type_="foreignkey")
        batch_op.drop_column("taxonomy")

