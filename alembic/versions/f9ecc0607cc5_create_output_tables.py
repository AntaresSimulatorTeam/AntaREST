"""create output tables

Revision ID: f9ecc0607cc5
Revises: 9770c0960334
Create Date: 2025-12-24 10:27:58.254977

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f9ecc0607cc5"
down_revision = "8a9a91f6a2bc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "output_v2_metadata",
        sa.Column("study_id", sa.String(), nullable=False, primary_key=True),
        sa.Column("output_name", sa.String(), nullable=False, primary_key=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("synthesis", sa.Boolean(), nullable=False),
        sa.Column("by_year", sa.Boolean(), nullable=False),
        sa.Column("nb_years", sa.Integer(), nullable=False),
        sa.Column("start_month", sa.Integer(), nullable=False),
        sa.Column("january_first_weekday", sa.Integer(), nullable=False),
        sa.Column("leap_year", sa.Boolean(), nullable=False),
        sa.Column("start_day", sa.Integer(), nullable=False),
        sa.Column("end_day", sa.Integer(), nullable=False),
        sa.Column("first_weekday", sa.Integer(), nullable=False),
    )
    op.create_table(
        "output_v2_logs",
        sa.Column("study_id", sa.String(), primary_key=True, nullable=False),
        sa.Column("output_id", sa.String(), primary_key=True, nullable=False),
        sa.Column("out", sa.String(), nullable=True),
        sa.Column("err", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id", "output_id"],
            ["output_v2_metadata.study_id", "output_v2_metadata.output_name"],
            ondelete="CASCADE",
        ),
    )
    op.create_table(
        "output_v2_variables",
        sa.Column("study_id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("output_id", sa.String(), primary_key=True, nullable=False),
        sa.Column("variables_list_version", sa.Integer(), nullable=False),
        sa.Column("variables_list", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "output_id"],
            ["output_v2_metadata.study_id", "output_v2_metadata.output_name"],
            ondelete="CASCADE",
        ),
    )


def downgrade():
    op.drop_table("output_v2_variables")
    op.drop_table("output_v2_logs")
    op.drop_table("output_v2_metadata")
