"""Make all managed studies folder path end with id

Revision ID: fa59340767b0
Revises: 9ba7fc46d4a0
Create Date: 2025-07-21 12:16:43.213036

"""

import sqlalchemy as sa
from sqlalchemy.sql import and_, case, column, exists, literal, not_, or_, table, update

from alembic import op

# revision identifiers, used by Alembic.
revision = "fa59340767b0"
down_revision = "9ba7fc46d4a0"
branch_labels = None
depends_on = None


def upgrade():
    """
    This update fixes an incident with the folder path of some managed studies.
    Sometimes, a study's folder does not end with its own ID.
    So this function add the ID to the end of the folder path if it is not already there.
    """
    # Create db connection
    bind = op.get_bind()

    type_string = sa.String(length=256)
    study_table = table("study", column("id", type_string), column("folder", type_string), column("type", type_string))

    rawstudy_table = table("rawstudy", column("id", type_string), column("workspace", type_string))

    # add id to folder, handle case with and without a trailing slash
    add_id_exp = case(
        (
            study_table.c.folder.like("%/"),
            study_table.c.folder + study_table.c.id,
        ),
        else_=study_table.c.folder + literal("/") + study_table.c.id,
    )

    is_in_default_workspace_subq = exists().where(
        and_(rawstudy_table.c.id == study_table.c.id, rawstudy_table.c.workspace == "default")
    )

    # managed study = in default workspace or is variant
    is_managed = or_(is_in_default_workspace_subq, study_table.c.type == "variantstudy")

    # We're only interested in managed studies
    # whose folder name doesn't end with their own ID.
    where_clause = and_(
        study_table.c.folder.isnot(None),
        not_(study_table.c.folder.like(literal("%") + study_table.c.id)),
        is_managed,
    )

    stmt = update(study_table).where(where_clause).values(folder=add_id_exp)
    bind.execute(stmt)


def downgrade():
    """
    We cannot downgrade this migration because we cannot make the difference between a folder path that was
    correctly set and one that was incorrectly set.
    """
    pass
