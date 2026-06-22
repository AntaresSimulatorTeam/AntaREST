"""add_reserve_name_column

Revision ID: f50e7ed59478
Revises: 844f4a7cd371
Create Date: 2026-06-22 17:15:05.096474

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f50e7ed59478'
down_revision = '844f4a7cd371'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("reserve_definition") as batch_op:
        # First, create the column
        batch_op.add_column(sa.Column("name", sa.String(255), nullable=True))

        # Update the 'name' column to match the 'id' column for all existing rows
        op.execute("UPDATE your_table_name SET name = id")

        # Alter the column to be non-nullable now that it's filled
        op.alter_column('your_table_name', 'name', nullable=False)

def downgrade() -> None:
    with op.batch_alter_table("reserve_definition") as batch_op:
        batch_op.drop_column("name")
