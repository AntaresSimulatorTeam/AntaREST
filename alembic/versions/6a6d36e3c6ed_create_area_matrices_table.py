"""create_area_matrices_table

Revision ID: 6a6d36e3c6ed
Revises: 8f3d2a1b5c7e
Create Date: 2026-01-26 10:45:36.111886

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a6d36e3c6ed'
down_revision = "8f3d2a1b5c7e"
branch_labels = None
depends_on = None


def upgrade():
    study_id_col = sa.Column("study_id", sa.String(length=36), nullable=False)
    area_id_col = sa.Column("area_id", sa.String(length=255), nullable=False)
    matrix_id_col = sa.Column("matrix_id", sa.String(length=64), nullable=False)
    foreign_key_constraint = sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            ondelete="CASCADE"
        )

    # Load
    foreign_key_constraint.name = op.f("fk_load_study_id_area_id_area")
    op.create_table(
        "load",
        study_id_col,  area_id_col, matrix_id_col, foreign_key_constraint,
        sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f("pk_load")),
    )

    # Solar
    foreign_key_constraint.name = op.f("fk_solar_study_id_area_id_area")
    op.create_table(
        "solar",
        study_id_col,  area_id_col, matrix_id_col, foreign_key_constraint,
        sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f("pk_solar")),
    )

    # Wind
    foreign_key_constraint.name = op.f("fk_wind_study_id_area_id_area")
    op.create_table(
        "wind",
        study_id_col,  area_id_col, matrix_id_col, foreign_key_constraint,
        sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f("pk_wind")),
    )

    # Reserves
    foreign_key_constraint.name = op.f("fk_reserves_study_id_area_id_area")
    op.create_table(
        "reserves",
        study_id_col,  area_id_col, matrix_id_col, foreign_key_constraint,
        sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f("pk_reserves")),
    )

    # Misc-gen
    foreign_key_constraint.name = op.f("fk_misc_gen_study_id_area_id_area")
    op.create_table(
        "misc_gen",
        study_id_col,  area_id_col, matrix_id_col, foreign_key_constraint,
        sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f("pk_misc_gen")),
    )

def downgrade():
    op.drop_table("load")
    op.drop_table("solar")
    op.drop_table("wind")
    op.drop_table("reserves")
    op.drop_table("misc_gen")
