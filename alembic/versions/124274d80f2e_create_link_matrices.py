"""create_link_matrices

Revision ID: 124274d80f2e
Revises: 9c4e7f2a3b1d
Create Date: 2026-01-30 13:37:09.850694

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '124274d80f2e'
down_revision = '9c4e7f2a3b1d'
branch_labels = None
depends_on = None


def upgrade():
    study_id_col = sa.Column("study_id", sa.String(length=36), nullable=False)
    area1_col = sa.Column("area1_id", sa.String(length=255), nullable=False)
    area2_col = sa.Column("area2_id", sa.String(length=255), nullable=False)
    matrix_id_col = sa.Column("matrix_id", sa.String(length=64), nullable=False)
    foreign_key_constraint = sa.ForeignKeyConstraint(
        ["study_id", "area1_id", "area2_id"],
        ["link.study_id", "link.area1", "link.area2"],
        ondelete="CASCADE"
    )

    # Series
    foreign_key_constraint.name = op.f("fk_link_series")
    op.create_table(
        "link_series",
        study_id_col, area1_col, area2_col, matrix_id_col, foreign_key_constraint,
        sa.PrimaryKeyConstraint("study_id", "area1_id", "area2_id", name=op.f("pk_link_series")),
    )

    # Direct capacity
    foreign_key_constraint.name = op.f("fk_link_direct_capacity")
    op.create_table(
        "link_direct_capacity",
        study_id_col, area1_col, area2_col, matrix_id_col, foreign_key_constraint,
        sa.PrimaryKeyConstraint("study_id", "area1_id", "area2_id", name=op.f("pk_link_direct_capacity")),
    )

    # Indirect capacity
    foreign_key_constraint.name = op.f("fk_link_indirect_capacity")
    op.create_table(
        "link_indirect_capacity",
        study_id_col, area1_col, area2_col, matrix_id_col, foreign_key_constraint,
        sa.PrimaryKeyConstraint("study_id", "area1_id", "area2_id", name=op.f("pk_link_indirect_capacity")),
    )

def downgrade():
    op.drop_table("link_series")
    op.drop_table("link_direct_capacity")
    op.drop_table("link_indirect_capacity")
