"""add_cascade_delete_for_sqlite

Revision ID: 490b80a84bb5
Revises: c0c4aaf84861
Create Date: 2024-10-11 11:38:45.108227

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '490b80a84bb5'
down_revision = 'c0c4aaf84861'
branch_labels = None
depends_on = None


def upgrade():
    _migrate(upgrade=True)

def downgrade():
    _migrate(upgrade=False)


def _migrate(upgrade: bool):
    # Use on_cascade=DELETE to avoid foreign keys issues in SQLite.
    # As it doesn't support dropping foreign keys, we have to do the migration ourselves.
    # https://www.sqlite.org/lang_altertable.html#otheralter
    # 1 - Create table with the right columns
    # 2 - Copy all the data from the old table inside the new one
    # 3 - Remove the old table
    # 4 - Rename the new table to have the old name

    dialect_name: str = op.get_context().dialect.name
    if dialect_name == "postgresql":
        return

    # =============================
    #  STUDY_ADDITIONAL_DATA
    # =============================

    op.create_table('study_additional_data_copy',
                    sa.Column('study_id', sa.String(length=36), nullable=False),
                    sa.Column('author', sa.String(length=255), nullable=True),
                    sa.Column('horizon', sa.String(), nullable=True),
                    sa.Column('patch', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE' if upgrade else None),
                    sa.PrimaryKeyConstraint('study_id')
                    )
    bind = op.get_bind()
    content = bind.execute(sa.text("SELECT * FROM study_additional_data"))
    for row in content:
        bind.execute(
            sa.text("INSERT INTO study_additional_data_copy (study_id, author, horizon, patch) VALUES (?,?,?,?)"),
            (row[0], row[1], row[2], row[3])
        )
    op.drop_table("study_additional_data")
    op.rename_table("study_additional_data_copy", "study_additional_data")

    # =============================
    #  RAW_METADATA
    # =============================

    op.create_table('rawstudycopy',
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('content_status', sa.Enum('VALID', 'WARNING', 'ERROR', name='studycontentstatus'),
                              nullable=True),
                    sa.Column('workspace', sa.String(length=255), nullable=False),
                    sa.Column('missing', sa.String(length=255), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['study.id'], ondelete='CASCADE' if upgrade else None),
                    sa.PrimaryKeyConstraint('id')
                    )
    with op.batch_alter_table("rawstudycopy", schema=None) as batch_op:
        if upgrade:
            batch_op.create_index(batch_op.f("ix_rawstudycopy_missing"), ["missing"], unique=False)
            batch_op.create_index(batch_op.f("ix_rawstudycopy_workspace"), ["workspace"], unique=False)
        else:
            batch_op.drop_index(batch_op.f("ix_rawstudycopy_missing"))
            batch_op.drop_index(batch_op.f("ix_rawstudycopy_workspace"))

    bind = op.get_bind()
    content = bind.execute(sa.text("SELECT * FROM rawstudy"))
    for row in content:
        bind.execute(
            sa.text("INSERT INTO rawstudycopy (id, content_status, workspace, missing) VALUES (?,?,?,?)"),
            (row[0], row[1], row[2], row[3])
        )
    op.drop_table("rawstudy")
    op.rename_table("rawstudycopy", "rawstudy")

    # =============================
    #  COMMAND BLOCK
    # =============================

    op.create_table(
        "commandblock_copy",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("study_id", sa.String(length=36), nullable=True),
        sa.Column("block_index", sa.Integer(), nullable=True),
        sa.Column("command", sa.String(length=255), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("args", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["variantstudy.id"],
            ondelete="CASCADE" if upgrade else None
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    bind = op.get_bind()
    content = bind.execute(sa.text("SELECT * FROM commandblock"))
    for row in content:
        bind.execute(
            sa.text("INSERT INTO commandblock_copy (id, study_id, block_index, command, version, args) VALUES (?,?,?,?,?,?)"),
            (row[0], row[1], row[2], row[3], row[4], row[5])
        )
    op.alter_column(table_name="commandblock_copy", column_name="block_index", new_column_name="index")
    op.drop_table("commandblock")
    op.rename_table("commandblock_copy", "commandblock")

    # =============================
    #  VARIANT STUDY SNAPSHOT
    # =============================

    op.create_table(
        "variant_study_snapshot_copy",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column('last_executed_command', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["variantstudy.id"],
            ondelete="CASCADE" if upgrade else None
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    bind = op.get_bind()
    content = bind.execute(sa.text("SELECT * FROM variant_study_snapshot"))
    for row in content:
        bind.execute(
            sa.text("INSERT INTO variant_study_snapshot_copy (id, created_at, last_executed_command) VALUES (?,?,?)"),
            (row[0], row[1], row[2])
        )
    op.drop_table("variant_study_snapshot")
    op.rename_table("variant_study_snapshot_copy", "variant_study_snapshot")

    # =============================
    #  VARIANT STUDY
    # =============================

    op.create_table(
        "variantstudy_copy",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column('generation_task', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["study.id"],
            ondelete="CASCADE" if upgrade else None
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    bind = op.get_bind()
    content = bind.execute(sa.text("SELECT * FROM variantstudy"))
    for row in content:
        bind.execute(
            sa.text("INSERT INTO variantstudy_copy (id, generation_task) VALUES (?,?)"),
            (row[0], row[1])
        )
    op.drop_table("variantstudy")
    op.rename_table("variantstudy_copy", "variantstudy")

    # =============================
    #  GROUP METADATA
    # =============================

    op.create_table('groupmetadatacopy',
                    sa.Column('group_id', sa.String(length=36), nullable=False),
                    sa.Column('study_id', sa.String(length=36), nullable=False),
                    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete="CASCADE" if upgrade else None),
                    sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete="CASCADE" if upgrade else None)
                    )
    with op.batch_alter_table("groupmetadatacopy", schema=None) as batch_op:
        if upgrade:
            batch_op.create_index(batch_op.f("ix_groupmetadatacopy_group_id"), ["group_id"], unique=False)
            batch_op.create_index(batch_op.f("ix_groupmetadatacopy_study_id"), ["study_id"], unique=False)
        else:
            batch_op.drop_index(batch_op.f("ix_groupmetadatacopy_group_id"))
            batch_op.drop_index(batch_op.f("ix_groupmetadatacopy_study_id"))
    bind = op.get_bind()
    content = bind.execute(sa.text("SELECT * FROM group_metadata"))
    for row in content:
        bind.execute(
            sa.text("INSERT INTO groupmetadatacopy (group_id, study_id) VALUES (?,?)"),
            (row[0], row[1])
        )
    op.drop_table("group_metadata")
    op.rename_table("groupmetadatacopy", "group_metadata")

