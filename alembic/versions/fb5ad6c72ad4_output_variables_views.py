"""output_variables_views

Revision ID: fb5ad6c72ad4
Revises: 0b2141573d50
Create Date: 2025-11-10 13:34:36.786282

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb5ad6c72ad4'
down_revision = '0b2141573d50'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "output_variables_views",
        sa.Column('id', sa.String(), nullable=False),
        sa.Column("study_id", sa.String(), nullable=False),
        sa.Column("output_id", sa.String(), nullable=False),
        sa.Column("type", sa.Enum('AREA', 'LINK', 'THERMAL', 'RENEWABLE', 'SHORT_TERM_STORAGE', name='outputvariablestype'), nullable=False),
        sa.Column("frequency", sa.Enum('HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY', 'ANNUAL', name='matrixfrequency'), nullable=False),
        sa.Column("variable_name", sa.String(), nullable=False),

        sa.Column("area_id", sa.String(), nullable=True),
        sa.Column("area_from_id", sa.String(), nullable=True),
        sa.Column("area_to_id", sa.String(), nullable=True),
        sa.Column("thermal_id", sa.String(), nullable=True),
        sa.Column("renewable_id", sa.String(), nullable=True),
        sa.Column("st_storage_id", sa.String(), nullable=True),

        sa.Column("matrix_id", sa.String(), nullable=False),
        sa.Column("last_read", sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matrix_id"], ["matrix.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("output_variables_views", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_output_variables_views_study_id"), ["study_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_output_variables_views_output_id"), ["output_id"], unique=False)


def downgrade():
    op.drop_table('output_variables_views')
