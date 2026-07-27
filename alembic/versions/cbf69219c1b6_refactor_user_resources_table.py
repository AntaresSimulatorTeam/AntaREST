"""refactor_user_resources_table

Revision ID: cbf69219c1b6
Revises: d84134f661a9
Create Date: 2026-07-27 10:32:49.507698

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cbf69219c1b6'
down_revision = 'd84134f661a9'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("user_resources")

    op.create_table(
        "user_resources",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("resource_type", sa.Enum(name="resourcetype"), nullable=False),
        sa.Column("blob_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
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

    # Create indexes
    op.create_index("ix_user_resources_parent_id", "user_resources", ["parent_id"])
    # Create unique constraint to prevent duplicate user resources names under the same parent
    op.create_index("idx_user_resources_name_parent_unique", "user_resources",["name", "parent_id"], unique=True)


def downgrade() -> None:
    op.drop_table("user_resources")

    op.create_table(
        "user_resources",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.Enum(name="resourcetype"), nullable=False),
        sa.Column("blob_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_user_resource_study_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "path", name=op.f("pk_user_resources")),
    )
