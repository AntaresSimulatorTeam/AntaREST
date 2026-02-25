"""add_thematic_trimming_table

Revision ID: 562d4e1bd95d
Revises: c20d6b990db0
Create Date: 2026-02-24 17:18:50.260580

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '562d4e1bd95d'
down_revision = 'c20d6b990db0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "thematic_trimming",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("thematic_trimming", sa.JSON, nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name="fk_thematic_trimming_study_id_study",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", name="pk_thematic_trimming"),
    )

def downgrade():
    op.drop_table("thematic_trimming")
