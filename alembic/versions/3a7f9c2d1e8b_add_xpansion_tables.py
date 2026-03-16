"""add_xpansion_tables

Revision ID: 3a7f9c2d1e8b
Revises: 6f8e2a9c1b3d
Create Date: 2026-03-06 12:08:58.827623

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3a7f9c2d1e8b"
down_revision = "6f8e2a9c1b3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "xpansion_settings",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("master", sa.Enum("integer", "relaxed", name="xpansion_master"), nullable=False),
        sa.Column("uc_type", sa.Enum("expansion_fast", "expansion_accurate", name="xpansion_uc_type"), nullable=False),
        sa.Column("optimality_gap", sa.Float(), nullable=False),
        sa.Column("relative_gap", sa.Float(), nullable=False),
        sa.Column("relaxed_optimality_gap", sa.Float(), nullable=False),
        sa.Column("max_iteration", sa.Integer(), nullable=False),
        sa.Column("solver", sa.Enum("Cbc", "Coin", "Xpress", name="xpansion_solver"), nullable=False),
        sa.Column("log_level", sa.Integer(), nullable=False),
        sa.Column("separation_parameter", sa.Float(), nullable=False),
        sa.Column("batch_size", sa.Integer(), nullable=False),
        sa.Column("yearly_weights", sa.String(), nullable=False),
        sa.Column("additional_constraints", sa.String(), nullable=False),
        sa.Column("timelimit", sa.Integer(), nullable=False),
        sa.Column("master_solution_tolerance", sa.Float(), nullable=False),
        sa.Column("cut_coefficient_tolerance", sa.Float(), nullable=False),
        sa.Column("sensitivity_epsilon", sa.Float(), nullable=False),
        sa.Column("sensitivity_capex", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["study.id"],
            name=op.f("fk_xpansion_settings_study_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", name=op.f("pk_xpansion_settings")),
    )

    op.create_table(
        "xpansion_candidate",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("link_area_from", sa.String(length=255), nullable=False),
        sa.Column("link_area_to", sa.String(length=255), nullable=False),
        sa.Column("annual_cost_per_mw", sa.Float(), nullable=False),
        sa.Column("unit_size", sa.Float(), nullable=True),
        sa.Column("max_units", sa.Integer(), nullable=True),
        sa.Column("max_investment", sa.Float(), nullable=True),
        sa.Column("already_installed_capacity", sa.Integer(), nullable=True),
        sa.Column("link_profile", sa.String(length=255), nullable=True),
        sa.Column("already_installed_link_profile", sa.String(length=255), nullable=True),
        sa.Column("direct_link_profile", sa.String(length=255), nullable=True),
        sa.Column("indirect_link_profile", sa.String(length=255), nullable=True),
        sa.Column("already_installed_direct_link_profile", sa.String(length=255), nullable=True),
        sa.Column("already_installed_indirect_link_profile", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["xpansion_settings.study_id"],
            name=op.f("fk_xpansion_candidate_settings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["study_id", "link_area_from", "link_area_to"],
            ["link.study_id", "link.area1", "link.area2"],
            name=op.f("fk_xpansion_candidate_link"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "name", name=op.f("pk_xpansion_candidate")),
    )

    op.create_table(
        "xpansion_sensitivity_projection",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "candidate_name"],
            ["xpansion_candidate.study_id", "xpansion_candidate.name"],
            name=op.f("fk_xpansion_sensitivity_projection_candidate"),
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "candidate_name", name=op.f("pk_xpansion_sensitivity_projection")),
    )

    op.create_table(
        "xpansion_adequacy_criterion",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("stopping_threshold", sa.Float(), nullable=False),
        sa.Column("criterion_count_threshold", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["xpansion_settings.study_id"],
            name=op.f("fk_xpansion_adequacy_criterion_settings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", name=op.f("pk_xpansion_adequacy_criterion")),
    )

    op.create_table(
        "xpansion_adequacy_pattern",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area", sa.String(length=255), nullable=False),
        sa.Column("criterion", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id"],
            ["xpansion_adequacy_criterion.study_id"],
            name=op.f("fk_xpansion_adequacy_pattern_criterion"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["study_id", "area"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_xpansion_adequacy_pattern_study_id_area_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area", name=op.f("pk_xpansion_adequacy_pattern")),
    )


def downgrade() -> None:
    op.drop_table("xpansion_adequacy_pattern")
    op.drop_table("xpansion_adequacy_criterion")
    op.drop_table("xpansion_sensitivity_projection")
    op.drop_table("xpansion_candidate")
    op.drop_table("xpansion_settings")
    if op.get_context().dialect.name == "postgresql":
        sa.Enum(name="xpansion_solver").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="xpansion_uc_type").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="xpansion_master").drop(op.get_bind(), checkfirst=True)
