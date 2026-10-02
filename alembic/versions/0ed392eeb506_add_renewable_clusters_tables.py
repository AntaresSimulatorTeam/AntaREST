"""add_renewable_clusters_tables

Revision ID: 0ed392eeb506
Revises: ae838d5fd166
Create Date: 2026-02-16 10:22:20.517377

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ed392eeb506'
down_revision = 'ae838d5fd166'
branch_labels = None
depends_on = None


def upgrade():
    study_id_col = sa.Column("study_id", sa.String(length=36), nullable=False)
    area_id_col = sa.Column("area_id", sa.String(length=255), nullable=False)
    renewable_id_col = sa.Column("renewable_id", sa.String(length=255), nullable=False)
    matrix_id_col = sa.Column("matrix_id", sa.String(length=64), nullable=False)

    op.create_table(
        "renewable_cluster",
        study_id_col,
        area_id_col,
        renewable_id_col,
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit_count", sa.Integer(), nullable=False),
        sa.Column("nominal_capacity", sa.Float(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("group", sa.String(length=255), nullable=False),
        sa.Column("ts_interpretation", sa.Enum("power-generation", "production-factor", name="renewabletsinterpretation"), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_renewable_cluster_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "renewable_id", name=op.f("pk_renewable_cluster")),
    )

    op.create_table(
        "renewable_series",
        study_id_col,
        area_id_col,
        renewable_id_col,
        matrix_id_col,
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "renewable_id"],
            ["renewable_cluster.study_id", "renewable_cluster.area_id", "renewable_cluster.renewable_id"],
            name=op.f("fk_renewable_series_renewable_cluster"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "renewable_id", name=op.f("pk_renewable_series")),
    )


def downgrade():
    op.drop_table("renewable_cluster")
    op.drop_table("renewable_series")
    if op.get_context().dialect.name == "postgresql":
        sa.Enum(name="renewabletsinterpretation").drop(op.get_bind(), checkfirst=True)
