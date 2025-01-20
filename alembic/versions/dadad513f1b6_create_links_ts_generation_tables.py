"""create_links_ts_generation_tables

Revision ID: dadad513f1b6
Revises: bae9c99bc42d
Create Date: 2025-01-20 10:11:01.293931

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dadad513f1b6'
down_revision = 'bae9c99bc42d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "study_nb_ts_gen",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("links", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["study.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "links_ts_gen_properties",
        sa.Column("id", sa.Integer()),
        sa.Column("area_from", sa.String(), nullable=False),
        sa.Column("area_to", sa.String(), nullable=False),
        sa.Column("prepro", sa.String(), nullable=False),
        sa.Column("modulation", sa.String(), nullable=False),
        sa.Column("unit_count", sa.Integer(), nullable=False),
        sa.Column("nominal_capacity", sa.Float(), nullable=False),
        sa.Column("law_planned", sa.Enum('uniform', 'geometric', name='lawplanned'), nullable=False),
        sa.Column("law_forced", sa.Enum('uniform', 'geometric', name='lawforced'), nullable=False),
        sa.Column("volatility_planned", sa.String(), nullable=False),
        sa.Column("volatility_forced", sa.String(), nullable=False),
        sa.Column("force_no_generation", sa.Boolean(), nullable=False),
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade():
    op.drop_table("study_nb_ts_gen")
    op.drop_table("links_ts_gen_properties")
