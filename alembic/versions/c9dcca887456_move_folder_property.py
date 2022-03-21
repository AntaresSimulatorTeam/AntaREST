"""move_folder_property

Revision ID: c9dcca887456
Revises: ef72a8a1c9cf
Create Date: 2022-03-15 09:13:19.215802

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = 'c9dcca887456'
down_revision = 'ef72a8a1c9cf'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('study', schema=None) as batch_op:
        batch_op.add_column(sa.Column('folder', sa.String(), nullable=True))

    # data migration
    connexion: Connection = op.get_bind()
    raw_studies = connexion.execute("SELECT id,folder FROM rawstudy")
    for raw_study in raw_studies:
        connexion.execute(text(f"UPDATE study SET folder= :folder WHERE id='{raw_study[0]}'"),
                          folder=raw_study[1])
    # end of data migration

    with op.batch_alter_table('rawstudy', schema=None) as batch_op:
        batch_op.drop_column('folder')


def downgrade():
    with op.batch_alter_table('rawstudy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('folder', sa.VARCHAR(), nullable=True))

    # data migration
    connexion: Connection = op.get_bind()
    raw_studies = connexion.execute("SELECT study.id,study.folder FROM study JOIN rawstudy ON study.id = rawstudy.id")
    for raw_study in raw_studies:
        connexion.execute(text(f"UPDATE rawstudy SET folder= :folder WHERE id='{raw_study[0]}'"),
                          folder=raw_study[1])
    # end of data migration

    with op.batch_alter_table('study', schema=None) as batch_op:
        batch_op.drop_column('folder')
