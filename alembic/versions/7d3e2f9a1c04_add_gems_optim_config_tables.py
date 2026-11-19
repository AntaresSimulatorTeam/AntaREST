"""add_gems_optim_config_tables

Revision ID: 7d3e2f9a1c04
Revises: 1c8b0b189035
Create Date: 2026-11-13 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = '7d3e2f9a1c04'
down_revision = '1c8b0b189035'
branch_labels = None
depends_on = None


def upgrade():
    gems_out_of_bounds_mode_enum = sa.Enum("cyclic", "drop", name="gemsoutofboundsmode")

    op.create_table(
        "gems_optim_config",
        study_data_id_col(),
        sa.Column("time_scope", sa.String(), nullable=True),
        sa.Column("scenario_scope", sa.String(), nullable=True),
        sa.Column("solver_options", sa.String(), nullable=True),
        sa.Column("resolution", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], name="fk_gems_optim_config", ondelete="CASCADE"),
    )

    # Out of Bound processing
    op.create_table(
        "gems_optim_config_oob_processing",
        study_data_id_col(primary_key=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("constraint_id", sa.String(length=255), nullable=False),
        sa.Column("mode", gems_out_of_bounds_mode_enum, nullable=False),
        sa.PrimaryKeyConstraint("study_id", "library_id", "model_id", "constraint_id", name="pk_gems_optim_config_oob_processing"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id", "constraint_id"],
            ["gems_models_constraints.study_data_id", "gems_models_constraints.library_id", "gems_models_constraints.model_id", "gems_models_constraints.id"],
            name="fk_gems_optim_config_oob_processing",
            ondelete="CASCADE",
        )
    )

    # Heuristics
    op.create_table(
        "gems_optim_config_heuristics",
        study_data_id_col(primary_key=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("data", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("study_id", "library_id", "model_id", name="pk_gems_optim_config_heuristics"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id"],
            ["gems_models.study_data_id", "gems_models.library_id", "gems_models.id"],
            name="fk_gems_optim_config_heuristics",
            ondelete="CASCADE",
        )
    )

    # Model decomposition
    ## Variables
    op.create_table(
        "gems_optim_config_model_decomposition_variables",
        study_data_id_col(primary_key=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("variable_id", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("study_id", "library_id", "model_id", "variable_id", name="pk_gems_optim_config_model_decomposition_variables"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id", "variable_id"],
            ["gems_models_variables.study_data_id", "gems_models_variables.library_id",
             "gems_models_variables.model_id", "gems_models_variables.id"],
            name="fk_gems_optim_config_model_decomposition_variables",
            ondelete="CASCADE",
        )
    )

    ## Constraints
    op.create_table(
        "gems_optim_config_model_decomposition_constraints",
        study_data_id_col(primary_key=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("constraint_id", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("study_id", "library_id", "model_id", "constraint_id",
                                name="pk_gems_optim_config_model_decomposition_constraints"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id", "constraint_id"],
            ["gems_models_constraints.study_data_id", "gems_models_constraints.library_id",
             "gems_models_constraints.model_id", "gems_models_constraints.id"],
            name="fk_gems_optim_config_model_decomposition_constraints",
            ondelete="CASCADE",
        )
    )

    ## Objective contribution
    op.create_table(
        "gems_optim_config_model_decomposition_objective_contributions",
        study_data_id_col(primary_key=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("objective_contribution_id", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("study_id", "library_id", "model_id", "objective_contribution_id",
                                name="pk_gems_optim_config_model_decomposition_objective_contributions"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id", "objective_contribution_id"],
            ["gems_models_objective_contributions.study_data_id", "gems_models_objective_contributions.library_id",
             "gems_models_objective_contributions.model_id", "gems_models_objective_contributions.id"],
            name="fk_gems_optim_config_model_decomposition_objective_contributions",
            ondelete="CASCADE",
        )
    )


def downgrade():
    op.drop_table("gems_optim_config_oob_processing")
    op.drop_table("gems_optim_config_heuristics")
    op.drop_table("gems_optim_config_model_decomposition_variables")
    op.drop_table("gems_optim_config_model_decomposition_constraints")
    op.drop_table("gems_optim_config_model_decomposition_objective_contributions")
    op.drop_table("gems_optim_config")
