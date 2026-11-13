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
    op.create_table(
        "gems_optim_config",
        study_data_id_col(),
        sa.Column("time_scope", sa.String(), nullable=True),
        sa.Column("scenario_scope", sa.String(), nullable=True),
        sa.Column("solver_options", sa.String(), nullable=True),
        sa.Column("resolution", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["study_data_id"], ["study_data.study_data_id"], name="fk_gems_optim_config", ondelete="CASCADE"),
    )

    op.create_table(
        "gems_optim_config_models",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        study_data_id_col(primary_key=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("variable_id", sa.String(length=255), nullable=True),
        sa.Column("constraint_id", sa.String(length=255), nullable=True),
        sa.Column("objective_contribution_id", sa.String(length=255), nullable=True),
        sa.Column("out_of_bounds_mode", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("heuristics", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["study_data_id"], ["gems_optim_config.study_data_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "model_id", "library_id"],
            ["gems_models.study_data_id", "gems_models.id", "gems_models.library_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id", "variable_id"],
            [
                "gems_models_variables.study_data_id",
                "gems_models_variables.library_id",
                "gems_models_variables.model_id",
                "gems_models_variables.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id", "constraint_id"],
            [
                "gems_models_constraints.study_data_id",
                "gems_models_constraints.library_id",
                "gems_models_constraints.model_id",
                "gems_models_constraints.id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id", "objective_contribution_id"],
            [
                "gems_models_objective_contributions.study_data_id",
                "gems_models_objective_contributions.library_id",
                "gems_models_objective_contributions.model_id",
                "gems_models_objective_contributions.id",
            ],
            ondelete="CASCADE",
        ),
    )


def downgrade():
    op.drop_table("gems_optim_config_models")
    op.drop_table("gems_optim_config")
