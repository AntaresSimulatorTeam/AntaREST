"""
Remove study additional data to add their fields to the study class
Revision ID:
Down revision: 0b2141573d50
"""

import sqlalchemy as sa  # type: ignore

from alembic import op

revision = "9du891hc3051"
down_revision = "0b2141573d50"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("study") as batch_op:
        batch_op.add_column(sa.Column("editor", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("horizon", sa.String(), nullable=True))

    # It's not that simple to copy data from one table to another in a database-agnostic way.
    # We use correlated subqueries which seem to be the more standard approach, althoug it
    # might not be the most efficient for example for postgresql.
    conn = op.get_bind()
    study = sa.table("study", sa.column("id"), sa.column("editor"), sa.column("author"), sa.column("horizon"))
    sad = sa.table(
        "study_additional_data", sa.column("study_id"), sa.column("editor"), sa.column("author"), sa.column("horizon")
    )

    conn.execute(
        study.update()
        .where(sa.exists().where(sad.c.study_id == study.c.id))
        .values(
            editor=sa.select(sad.c.editor).where(sad.c.study_id == study.c.id).scalar_subquery(),
            author=sa.select(sad.c.author).where(sad.c.study_id == study.c.id).scalar_subquery(),
            horizon=sa.select(sad.c.horizon).where(sad.c.study_id == study.c.id).scalar_subquery(),
        )
    )


def downgrade():
    with op.batch_alter_table("study") as batch_op:
        batch_op.drop_column("editor")
        batch_op.drop_column("horizon")
