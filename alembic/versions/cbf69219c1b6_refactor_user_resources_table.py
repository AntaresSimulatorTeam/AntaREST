"""refactor_user_resources_table

Revision ID: cbf69219c1b6
Revises: d84134f661a9
Create Date: 2026-07-27 10:32:49.507698

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cbf69219c1b6'
down_revision = 'd84134f661a9'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("user_resources")

    if op.get_context().dialect.name == "postgresql":
        # This enum was introduced in a previous migration, so we should not recreate it.
        # PostgreSQL does not handle this easily, so we have to use its own ENUM type to make it work.
        resource_type_enum = postgresql.ENUM(name="resourcetype",create_type=False)
    else:
        resource_type_enum = sa.Enum("file", "folder", name="resourcetype")

    op.create_table(
        "user_resources",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("resource_type", resource_type_enum, nullable=False),
        sa.Column("blob_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study_data.study_id"],
            name=op.f("fk_user_resource_study_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["user_resources.id"],
            name=op.f("fk_user_resource_parent_id"),
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_resources")

    if op.get_context().dialect.name == "postgresql":
        resource_type_enum = postgresql.ENUM(name="resourcetype", create_type=False)
    else:
        resource_type_enum = sa.Enum("file", "folder", name="resourcetype")

    op.create_table(
        "user_resources",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("resource_type", resource_type_enum, nullable=False),
        sa.Column("blob_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study_data.study_id"],
            name=op.f("fk_user_resource_study_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "path", name=op.f("pk_user_resources")),
    )
