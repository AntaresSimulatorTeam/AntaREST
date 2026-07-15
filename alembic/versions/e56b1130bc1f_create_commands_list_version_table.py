"""create_commands_list_version_table

Revision ID: e56b1130bc1f
Revises: 665f7b1d7575
Create Date: 2026-07-13 15:35:50.408218

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import column, table
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = 'e56b1130bc1f'
down_revision = '665f7b1d7575'
branch_labels = None
depends_on = None


def upgrade():
    # First, perform the operation with the least amount of risk
    with op.batch_alter_table('variant_study_snapshot', schema=None) as batch_op:
        batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="0"))
        batch_op.drop_column('created_at')

    # Create a new table linking variant commands to a "version" to avoid concurrent modification
    op.create_table(
        "commands_list_version",
        sa.Column("variant_id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("version",  sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["variantstudy.id"],
            name=op.f("fk_commmands_list_version_variantstudy_id"),
            ondelete="CASCADE",
        ),
    )

    # Create db connection
    bind = op.get_bind()
    session = Session(bind=bind)

    # Gathers all variant study ids
    result = session.query(table('variantstudy', column('id'))).all()
    if not result:
        # Means there are no variant studies in the database
        return
    data_to_insert = [{"variant_id": variant_id, "version": 0} for variant_id, in result]

    # Insert values to fill the newly created table
    sql = sa.text("INSERT INTO commands_list_version (variant_id, version) VALUES (:variant_id, :version)")
    bind.execute(sql, data_to_insert)


def downgrade():
    op.drop_table("commands_list_version")

    with op.batch_alter_table('variant_study_snapshot', schema=None) as batch_op:
        batch_op.drop_column('version')
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
