"""add editor field to study and study_additional_data tables

Revision ID: a8c6e9d47b12
Revises: 9ba7fc46d4a0
Create Date: 2025-06-24 10:15:00.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8c6e9d47b12'
down_revision = '9ba7fc46d4a0'
branch_labels = None
depends_on = None


def upgrade():
    # Add editor column to the study_additional_data table
    with op.batch_alter_table('study_additional_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('editor', sa.String(255), nullable=True, server_default="Unknown"))


def downgrade():
    # Remove editor column from the study_additional_data table
    with op.batch_alter_table('study_additional_data', schema=None) as batch_op:
        batch_op.drop_column('editor')
