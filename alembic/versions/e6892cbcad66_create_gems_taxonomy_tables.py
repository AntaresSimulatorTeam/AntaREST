"""create_gems_taxonomy_tables

Revision ID: e6892cbcad66
Revises: 0974bca4078d
Create Date: 2026-09-16 18:01:40.372496

"""
from alembic import op
from sqlalchemy import Column, String, ForeignKeyConstraint

from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = 'e6892cbcad66'
down_revision = '0974bca4078d'
branch_labels = None
depends_on = None

NEW_FK_NAME = "fk_taxonomy_category"

def upgrade():
    op.create_table(
        "gems_taxonomy_metadata",
        study_data_id_col(),
        Column("id", String(255), nullable=False),
        Column("description", String(), nullable=True),
        ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], ondelete="CASCADE"),
    )

    op.create_table(
        "gems_taxonomy_categories",
        study_data_id_col(),
        Column("id", String(255), primary_key=True),
        Column("parent_category", String(255), nullable=True),
        Column("variables", String(), nullable=True),
        Column("parameters", String(), nullable=True),
        Column("ports", String(), nullable=True),
        Column("extra_outputs", String(), nullable=True),
        Column("properties", String(), nullable=True),
        Column("binding_constraints", String(), nullable=True),
        ForeignKeyConstraint(
            ["study_data_id", "parent_category"],
            ["gems_taxonomy_categories.study_data_id", "gems_taxonomy_categories.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(["study_data_id"], ["gems_taxonomy_metadata.study_data_id"], ondelete="CASCADE"),
    )

    with op.batch_alter_table("gems_models", schema=None) as batch_op:
        batch_op.create_foreign_key(
            NEW_FK_NAME,
            "gems_taxonomy_categories",
            ["study_data_id", "taxonomy_category"],
            ["study_data_id", "id"],
        )

def downgrade():
    with op.batch_alter_table("gems_models", schema=None) as batch_op:
        batch_op.drop_constraint(NEW_FK_NAME, type_="foreignkey")

    op.drop_table("gems_taxonomy_categories")
    op.drop_table("gems_taxonomy_metadata")