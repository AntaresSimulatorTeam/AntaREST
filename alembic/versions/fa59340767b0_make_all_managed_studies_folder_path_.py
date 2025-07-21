"""Make all managed studies folder path end with id

Revision ID: fa59340767b0
Revises: 9ba7fc46d4a0
Create Date: 2025-07-21 12:16:43.213036

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "fa59340767b0"
down_revision = "9ba7fc46d4a0"
branch_labels = None
depends_on = None


def upgrade():
    """
    This update fixes an incident with the folder path of some managed studies.
    Sometimes, a study's folder does not end with its own ID
    (as seen in the top entry of the image below), even though this should always be
    the case). So this function add the ID to the end of the folder path if it is not already there.
    """
    op.execute(
        sa.text("""
        UPDATE study AS s SET
            folder = (
                CASE
                    WHEN folder LIKE '%/' THEN 
                        folder || id
                    ELSE 
                        folder || '/' || id
                END
            )
        WHERE
            s.folder IS NOT NULL
            AND s.folder NOT LIKE '%' || id
            AND (
                EXISTS (
                    SELECT 1 FROM rawstudy r
                    WHERE s.id = r.id AND r.workspace = 'default'
                )
                OR s."type" = 'variantstudy'
            );
    """)
    )


def downgrade():
    """
    We cannot downgrade this migration because we cannot make the difference between a folder path that was
    correctly set and one that was incorrectly set.
    """
    pass
