"""create_gems_catalogs_table

Revision ID: 3302075bbdfd
Revises: 24984ccc44c6
Create Date: 2026-09-25 09:37:53.433715

"""

from alembic import op
import sqlalchemy as sa

from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "3302075bbdfd"
down_revision = "24984ccc44c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_gems_taxonomy_metadata_study_data_id_id",
        "gems_taxonomy_metadata",
        ["study_data_id", "id"],
        unique=True,
    )
    op.create_table(
        "gems_catalogs",
        study_data_id_col(primary_key=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("taxonomy", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_data_id"], ["study_data.study_data_id"], name="fk_gems_catalogs_study_data", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["study_data_id", "location"],
            ["gems_taxonomy_categories.study_data_id", "gems_taxonomy_categories.id"],
            name="fk_gems_catalogs_location",
        ),
        sa.ForeignKeyConstraint(
            ["study_data_id", "taxonomy"],
            ["gems_taxonomy_metadata.study_data_id", "gems_taxonomy_metadata.id"],
            name="fk_gems_catalogs_taxonomy",
        ),
        sa.PrimaryKeyConstraint("study_data_id", "id", name="pk_gems_catalogs"),
    )
    op.create_table(
        "gems_catalog_metrics",
        study_data_id_col(primary_key=False),
        sa.Column("catalog_id", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("terms_operator", sa.Enum("sum", "avg", name="gems_aggregation_operator"), nullable=False),
        sa.Column("time_operator", sa.Enum("sum", "avg", name="gems_aggregation_operator"), nullable=False),
        sa.Column("terms", sa.String(), nullable=True),
        sa.Column("breakdown", sa.String(), nullable=True),
        sa.Column("filter", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_data_id", "catalog_id"],
            ["gems_catalogs.study_data_id", "gems_catalogs.id"],
            name="fk_gems_catalog_metrics_catalog",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_data_id", "catalog_id", "id", name="pk_gems_catalog_metrics"),
    )


def downgrade() -> None:
    op.drop_table("gems_catalog_metrics")
    op.drop_table("gems_catalogs")
    op.drop_index("uq_gems_taxonomy_metadata_study_data_id_id", table_name="gems_taxonomy_metadata")
    sa.Enum(name="gems_aggregation_operator").drop(op.get_bind(), checkfirst=True)
