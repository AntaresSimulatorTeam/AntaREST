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
        batch_op.add_column(sa.Column('editor', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('horizon', sa.String(), nullable=True))

    bind = op.get_bind()
    bind.execute(text("UPDATE study s INNER JOIN study_additional_data sad ON s.id = sad.id SET s.editor = sad.editor, s.author = sad.author, s.horizon = sad.horizon;"))


def downgrade():
    with op.batch_alter_table("study") as batch_op:
        batch_op.drop_column('editor')
        batch_op.drop_column('horizon')