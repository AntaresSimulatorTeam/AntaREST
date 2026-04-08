"""add_binding_constraints_table

Revision ID: da32c69cfb49
Revises: 81typ5zz6v1y
Create Date: 2026-04-08 10:17:14.465486

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "da32c69cfb49"
down_revision = "81typ5zz6v1y"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table(
        "binding_constraint",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("constraint_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("time_step", sa.Enum("hourly", "daily", "weekly", name="bc_frequency"), nullable=False),
        sa.Column("operator", sa.Enum("less", "greater", "both", "equal", name="bc_operator"), nullable=False),
        sa.Column("comments", sa.String(), nullable=False),
        sa.Column("filter_year_by_year", sa.String(), nullable=True),
        sa.Column("filter_synthesis", sa.String(), nullable=True),
        sa.Column("group", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_binding_constraint_study_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "constraint_id", name=op.f("pk_binding_constraint")),
    )

    op.create_table(
        "binding_constraint_link_term",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("constraint_id", sa.String(length=255), nullable=False),
        sa.Column("area1", sa.String(length=255), nullable=False),
        sa.Column("area2", sa.String(length=255), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("offset", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id", "constraint_id"],
            ["binding_constraint.study_id", "binding_constraint.constraint_id"],
            name=op.f("fk_bc_link_term_constraint"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "study_id", "constraint_id", "area1", "area2", name=op.f("pk_binding_constraint_link_term")
        ),
    )

    op.create_table(
        "binding_constraint_cluster_term",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("constraint_id", sa.String(length=255), nullable=False),
        sa.Column("area", sa.String(length=255), nullable=False),
        sa.Column("cluster", sa.String(length=255), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("offset", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id", "constraint_id"],
            ["binding_constraint.study_id", "binding_constraint.constraint_id"],
            name=op.f("fk_bc_cluster_term_constraint"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "study_id", "constraint_id", "area", "cluster", name=op.f("pk_binding_constraint_cluster_term")
        ),
    )

    for table_name in (
        "binding_constraint_values_matrix",
        "binding_constraint_lt_matrix",
        "binding_constraint_gt_matrix",
        "binding_constraint_eq_matrix",
    ):
        op.create_table(
            table_name,
            sa.Column("study_id", sa.String(length=36), nullable=False),
            sa.Column("constraint_id", sa.String(length=255), nullable=False),
            sa.Column("matrix_id", sa.String(length=64), nullable=False),
            sa.ForeignKeyConstraint(
                ["study_id", "constraint_id"],
                ["binding_constraint.study_id", "binding_constraint.constraint_id"],
                name=op.f(f"fk_{table_name}_constraint"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("study_id", "constraint_id", name=op.f(f"pk_{table_name}")),
        )


def downgrade() -> None:
    for table_name in (
        "binding_constraint_eq_matrix",
        "binding_constraint_gt_matrix",
        "binding_constraint_lt_matrix",
        "binding_constraint_values_matrix",
    ):
        op.drop_table(table_name)

    op.drop_table("binding_constraint_cluster_term")
    op.drop_table("binding_constraint_link_term")
    op.drop_table("binding_constraint")

    sa.Enum(name="bc_operator").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="bc_frequency").drop(op.get_bind(), checkfirst=True)
