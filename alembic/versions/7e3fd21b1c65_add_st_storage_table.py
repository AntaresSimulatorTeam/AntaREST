"""add st storage table

Revision ID: 7e3fd21b1c65
Revises: f77c2a9e5d0c
Create Date: 2026-02-17 10:56:14.109723

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7e3fd21b1c65'
down_revision = 'f77c2a9e5d0c'
branch_labels = None
depends_on = None

matrix_tables = [
    "pmax_injection",
    "pmax_withdrawal",
    "lower_rule_curve",
    "upper_rule_curve",
    "inflows",
    "cost_injection",
    "cost_withdrawal",
    "cost_level",
    "variation_injection",
    "variation_withdrawal",
]

def upgrade():
    group_enum = sa.Enum("psp_open", "psp_closed", "pondage", "battery", "other1", "other2", "other3", "other4", "other5", name="group")
    variable_enum = sa.Enum("withdrawal", "injection", "netting", name="variable")
    operator_enum = sa.Enum("less", "greater", "equal", name="operator")

    op.create_table(
        "st_storage",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("group", group_enum, nullable=False),
        sa.Column("injection_nominal_capacity", sa.Float(), nullable=False),
        sa.Column("withdrawal_nominal_capacity", sa.Float(), nullable=False),
        sa.Column("reservoir_capacity", sa.Float(), nullable=False),
        sa.Column("efficiency", sa.Float(), nullable=False),
        sa.Column("initial_level", sa.Float(), nullable=False),
        sa.Column("initial_level_optim", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("efficiency_withdrawal", sa.Float(), nullable=True),
        sa.Column("penalize_variation_injection", sa.Boolean(), nullable=True),
        sa.Column("penalize_variation_withdrawal", sa.Boolean(), nullable=True),
        sa.Column("allow_overflow", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
                    name="fk_st_storage_area",
                    ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "id", name="pk_st_storage")
    )

    for table in matrix_tables:
        op.create_table(
            table,
            sa.Column("study_id", sa.String(length=36), nullable=False),
            sa.Column("area_id", sa.String(length=255), nullable=False),
            sa.Column("st_storage_id", sa.String(length=255), nullable=False),
            sa.Column("matrix_id", sa.String(length=64), nullable=False),
            sa.ForeignKeyConstraint(
                ["study_id", "area_id", "st_storage_id"],
                ["st_storage.study_id", "st_storage.area_id", "st_storage.id"],
                        name=f"fk_{table}_st_storage",
                        ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("study_id", "area_id", "st_storage_id", name=f"pk_{table}")
        )

    op.create_table(
        "st_storage_additional_constraint",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("st_storage_id", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("variable", variable_enum, nullable=False),
        sa.Column("operator", operator_enum, nullable=False),
        sa.Column("occurrences", sa.JSON, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "st_storage_id"],
            ["st_storage.study_id", "st_storage.area_id", "st_storage.id"],
                    name="fk_st_storage_additional_constraint",
                    ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "st_storage_id", "id", name="pk_st_storage_additional_constraint")
    )

    op.create_table(
        "st_storage_additional_constraint_matrix",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("st_storage_id", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("matrix_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id", "st_storage_id", "id"],
            ["st_storage_additional_constraint.study_id", "st_storage_additional_constraint.area_id", "st_storage_additional_constraint.st_storage_id", "st_storage_additional_constraint.id"],
            name="fk_st_storage_constraint_matrix_st_storage",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", "st_storage_id", "id", name="pk_st_storage_constraint_matrix")
    )

def downgrade():
    for table in matrix_tables:
        op.drop_table(table)

    op.drop_table("st_storage_additional_constraint_matrix")
    op.drop_table("st_storage_additional_constraint")
    op.drop_table("st_storage")

    if op.get_context().dialect.name == "postgresql":
        sa.Enum(name="group").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="variable").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="operator").drop(op.get_bind(), checkfirst=True)
