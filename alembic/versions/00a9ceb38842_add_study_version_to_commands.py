"""add_study_version_to_commands

Revision ID: 00a9ceb38842
Revises: b33e1f57a60c
Create Date: 2024-10-28 10:30:15.877468

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision = '00a9ceb38842'
down_revision = 'b33e1f57a60c'
branch_labels = None
depends_on = None


def upgrade():
    # Add new column with empty data
    with op.batch_alter_table("commandblock", schema=None) as batch_op:
        batch_op.add_column(sa.Column('study_version', sa.String(length=36), server_default="fake_version", nullable=False))

    # Create db connection
    bind = op.get_bind()
    session = Session(bind=bind)

    # Reference tables
    commandblock_table = table('commandblock', column('id'), column('study_id'))
    study_table = table('study', column('id'), column('version'))

    # Gathers commands by study_id
    commands = session.query(commandblock_table).all()
    mapping = {}
    for cmd in commands:
        cmd_id = cmd[0]
        study_id = cmd[1]
        mapping.setdefault(study_id, []).append(cmd_id)

    # Gets studies versions
    study_info = session.query(study_table).filter(study_table.c.id.in_(mapping)).all()

    # Clean orphan commands
    study_ids = {study_id for study_id, _ in study_info}
    ids_to_remove = {cmd_id for study_id, cmd_ids in mapping.items() if study_id not in study_ids for cmd_id in cmd_ids}
    bind.execute(commandblock_table.delete().where(commandblock_table.c.id.in_(ids_to_remove)))

    # Insert new values
    alter_table = table("commandblock", column("id"), column("study_id"), column("study_version"))
    scalar_subq = sa.select(study_table.c.version).where(study_table.c.id == alter_table.c.study_id).scalar_subquery()
    bind.execute(sa.update(alter_table).values(study_version=scalar_subq))


def downgrade():
    with op.batch_alter_table("commandblock", schema=None) as batch_op:
        batch_op.drop_column('study_version')
