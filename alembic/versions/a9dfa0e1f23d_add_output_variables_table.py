"""add_output_variables_table

Revision ID: a9dfa0e1f23d
Revises: d2942741ae68
Create Date: 2025-10-14 14:10:28.470792

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9dfa0e1f23d'
down_revision = 'd2942741ae68'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('output_variables',
   sa.Column('study_id', sa.String(length=36), nullable=False),
            sa.Column('output_id', sa.String(), nullable=False),
            sa.Column('variables_metadata_version', sa.Integer(), nullable=False),
            sa.Column('variables_metadata', sa.LargeBinary(), nullable=False),
            sa.ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("study_id", "output_id"),
    )


def downgrade():
    op.drop_table('output_variables')
