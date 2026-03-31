"""add_study_disk_space_analysis_table

Revises: c11cfe5728b0
Create Date: 2022-01-25 09:50:17.304650

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '81typ5zz6v1y'
down_revision = 'ebcae82af0c3'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "study_disk_space_analysis",
        sa.Column("study_id", sa.String(), nullable=False),
        sa.Column("disk_space_bytes", sa.BigInteger(), nullable=False),
        sa.Column("last_analysis_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("study_id", name="pk_study_disk_space_analysis"),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_study_disk_space_analysis_study_id", ondelete="CASCADE")
    )

def downgrade():
    op.drop_table("study_disk_space_analysis")