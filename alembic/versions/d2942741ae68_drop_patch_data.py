"""drop_patch_data

Revision ID: d2942741ae68
Revises: 6c3d9dbf678c
Create Date: 2025-08-12 10:50:39.475561

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d2942741ae68"
down_revision = "6c3d9dbf678c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("study_additional_data", schema=None) as batch_op:
        # Explanation:
        # in revision 490b80a84bb5_add_cascade_delete_for_sqlite which is run for non-postgres DB
        # (as the name does not imply ...) the table was copied without the index.
        # Therefore we must not try to delete it in that case.
        if op.get_context().dialect.name == "postgresql":
            batch_op.drop_index(batch_op.f("ix_study_additional_data_patch"))
        batch_op.drop_column(batch_op.f("patch"))


def downgrade():
    # Cannot restore deleted data
    with op.batch_alter_table("study_additional_data", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("patch", sa.String(), nullable=True),
        )
        batch_op.create_index(batch_op.f("ix_study_additional_data_patch"), ["patch"], unique=False)
