"""make studies path nullable

Revision ID: 1bb1c26c70d8
Revises: 40f4391430e7
Create Date: 2026-08-20 15:43:44.948640

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '1bb1c26c70d8'
down_revision = '40f4391430e7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("study", schema=None) as batch_op:
        batch_op.alter_column("path", existing_type=sa.String(), nullable=True)

    # Set the path to None for existing database-mode studies
    study_table = sa.table("study", sa.column("path", sa.String()), sa.column("storage_mode", sa.String()))
    op.execute(study_table.update().where(study_table.c.storage_mode == "DATABASE").values(path=None))

def downgrade():

    # Set the path to the study ID for existing database-mode studies
    study_table = sa.table("study", sa.column("id", sa.String()), sa.column("path", sa.String()))
    op.execute(
        study_table.update().where(study_table.c.path.is_(None)).values(path=study_table.c.id)
    )

    with op.batch_alter_table("study", schema=None) as batch_op:
        batch_op.alter_column("path", existing_type=sa.String(), nullable=False)