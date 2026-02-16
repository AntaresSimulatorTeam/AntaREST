"""add user resources table

Revision ID: f77c2a9e5d0c
Revises: ae838d5fd166
Create Date: 2026-02-16 11:55:05.930667

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f77c2a9e5d0c"
down_revision = "ae838d5fd166"
branch_labels = None
depends_on = None


def upgrade() -> None:
    resource_type_enum = sa.Enum("file", "folder", name="resourcetype")
    op.create_table(
        "user_resources",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("resource_type", resource_type_enum, nullable=False),
        sa.Column("blob_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_user_resource_study_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "path", name=op.f("pk_user_resources")),
    )


def downgrade() -> None:
    op.drop_table("user_resources")
    if op.get_context().dialect.name == "postgresql":
        sa.Enum(name="resourcetype").drop(op.get_bind(), checkfirst=True)
