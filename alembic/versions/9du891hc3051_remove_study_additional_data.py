"""
Remove study additional data to add their fields to the study class
Revision ID:
Down revision: 0b2141573d50
"""
import sqlalchemy as sa  # type: ignore
from alembic import op
from sqlalchemy import text

revision = "9du891hc3051"
down_revision = "0b2141573d50"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("study") as batch_op:
        batch_op.add_column(sa.Column('editor', sa.String(length=255)))
        batch_op.add_column(sa.Column('horizon', sa.String(), nullable=True))

    bind = op.get_bind()
    content = bind.execute(text("SELECT author, editor, horizon FROM study_additional_data"))
    for row in content:
        bind.execute(
            "INSERT INTO study (author, editor, horizon) VALUES (?, ?, ?)",
            (row[0], row[1], row[2])
        )


def downgrade():
    with op.batch_alter_table("study") as batch_op:
        batch_op.drop_column('editor')
        batch_op.drop_column('horizon')