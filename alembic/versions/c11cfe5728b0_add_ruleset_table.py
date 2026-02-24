"""add ruleset table

Revision ID: c11cfe5728b0
Revises: 7e3fd21b1c65
Create Date: 2026-02-24 09:10:06.132523

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c11cfe5728b0"
down_revision = "7e3fd21b1c65"
branch_labels = None
depends_on = None


def upgrade() -> None:
    scenario_type_enum = sa.Enum(
        "load",
        "thermal",
        "hydro",
        "wind",
        "solar",
        "ntc",
        "renewable",
        "bindingConstraints",
        "hydroInitialLevels",
        "hydroFinalLevels",
        "hydroGenerationPower",
        "shortTermStorageInflows",
        "shortTermStorageAdditionalConstraints",
        name="scenariotype",
    )

    op.create_table(
        "ruleset",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("ruleset_name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_ruleset", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", "ruleset_name", name="pk_ruleset"),
    )

    op.create_table(
        "active_ruleset",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("ruleset_name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "ruleset_name"],
            ["ruleset.study_id", "ruleset.ruleset_name"],
            name="fk_active_ruleset",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", name="pk_active_ruleset"),
    )

    op.create_table(
        "ruleset_area",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("ruleset_name", sa.String(length=255), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("scenario_type", scenario_type_enum, nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "ruleset_name"],
            ["ruleset.study_id", "ruleset.ruleset_name"],
            name="fk_ruleset_area",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "ruleset_name", "area_id", "scenario_type", name="pk_ruleset_area"),
    )

    op.create_table(
        "ruleset_link",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("ruleset_name", sa.String(length=255), nullable=False),
        sa.Column("link_id", sa.String(length=255), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "ruleset_name"],
            ["ruleset.study_id", "ruleset.ruleset_name"],
            name="fk_ruleset_link",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "ruleset_name", "link_id", name="pk_ruleset_link"),
    )

    op.create_table(
        "ruleset_bc_group",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("ruleset_name", sa.String(length=255), nullable=False),
        sa.Column("bc_group_id", sa.String(length=255), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "ruleset_name"],
            ["ruleset.study_id", "ruleset.ruleset_name"],
            name="fk_ruleset_bc_group",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "ruleset_name", "bc_group_id", name="pk_ruleset_bc_group"),
    )

    op.create_table(
        "ruleset_area_item",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("ruleset_name", sa.String(length=255), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("scenario_type", scenario_type_enum, nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "ruleset_name"],
            ["ruleset.study_id", "ruleset.ruleset_name"],
            name="fk_ruleset_area_item",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "study_id", "ruleset_name", "area_id", "item_id", "scenario_type", name="pk_ruleset_area_item"
        ),
    )

    op.create_table(
        "ruleset_area_item_constraint",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("ruleset_name", sa.String(length=255), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("constraint_id", sa.String(length=255), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "ruleset_name"],
            ["ruleset.study_id", "ruleset.ruleset_name"],
            name="fk_ruleset_area_item_constraint",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "study_id", "ruleset_name", "area_id", "item_id", "constraint_id", name="pk_ruleset_area_item_constraint"
        ),
    )


def downgrade() -> None:
    op.drop_table("ruleset_area")
    op.drop_table("ruleset_link")
    op.drop_table("ruleset_bc_group")
    op.drop_table("ruleset_area_item")
    op.drop_table("ruleset_area_item_constraint")
    op.drop_table("active_ruleset")
    op.drop_table("ruleset")

    if op.get_bind().dialect.name == "postgresql":
        sa.Enum(name="scenariotype").drop(op.get_bind(), checkfirst=True)
