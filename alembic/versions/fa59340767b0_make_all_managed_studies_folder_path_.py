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
    op.execute(
        sa.text("""
        UPDATE study AS s SET
            folder = (
                CASE
                    WHEN folder LIKE '%/' THEN concat(folder, id)
                    ELSE concat(concat(folder, '/'), id)
                END
            )
        WHERE
            s.folder IS NOT NULL
            AND s.folder NOT LIKE concat('%', id)
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
    pass
