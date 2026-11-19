"""add_gems_optim_config_tables

Revision ID: 7d3e2f9a1c04
Revises: 55ae4521e871
Create Date: 2026-11-13 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = '7d3e2f9a1c04'
down_revision = '55ae4521e871'
branch_labels = None
depends_on = None


def upgrade():
    gems_out_of_bounds_mode_enum = sa.Enum("cyclic", "drop", name="gemsoutofboundsmode")
    gems_decomposition_location_enum = sa.Enum("master", "subproblems", "master-and-subproblems", name="gemsdecompositionlocation")

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
        sa.PrimaryKeyConstraint("study_data_id", "library_id", "model_id", "constraint_id", name="pk_gems_optim_config_oob_processing"),
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
        sa.PrimaryKeyConstraint("study_data_id", "library_id", "model_id", name="pk_gems_optim_config_heuristics"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id"],
            ["gems_models.study_data_id", "gems_models.library_id", "gems_models.id"],
            name="fk_gems_optim_config_heuristics",
            ondelete="CASCADE",
        )
    )

    # Model decomposition
    def _create_model_decomposition_table(table_name: str, column_name: str, reference_table_name: str) -> None:
        op.create_table(
            table_name,
            study_data_id_col(primary_key=False),
            sa.Column("library_id", sa.String(length=255), nullable=False),
            sa.Column("model_id", sa.String(length=255), nullable=False),
            sa.Column(column_name, sa.String(length=255), nullable=False),
            sa.Column("location", gems_decomposition_location_enum, nullable=False),
            sa.PrimaryKeyConstraint("study_data_id", "library_id", "model_id", column_name,
                                    name=f"pk_{table_name}"),
            sa.ForeignKeyConstraint(
                ["study_data_id", "library_id", "model_id", column_name],
                [
                    f"{reference_table_name}.study_data_id",
                    f"{reference_table_name}.library_id",
                    f"{reference_table_name}.model_id",
                    f"{reference_table_name}.id"],
                name=f"fk_{table_name}",
                ondelete="CASCADE",
            )
        )

    _create_model_decomposition_table(
        table_name="gems_optim_config_model_decomposition_variables",
        column_name="variable_id",
        reference_table_name="gems_models_variables"
    )

    _create_model_decomposition_table(
        table_name="gems_optim_config_model_decomposition_constraints",
        column_name="constraint_id",
        reference_table_name="gems_models_constraints",
    )

    _create_model_decomposition_table(
        table_name="gems_optim_config_model_decomposition_objective_contributions",
        column_name="objective_contribution_id",
        reference_table_name="gems_models_objective_contributions",
    )

def downgrade():
    op.drop_table("gems_optim_config_oob_processing")
    op.drop_table("gems_optim_config_heuristics")
    op.drop_table("gems_optim_config_model_decomposition_variables")
    op.drop_table("gems_optim_config_model_decomposition_constraints")
    op.drop_table("gems_optim_config_model_decomposition_objective_contributions")
    op.drop_table("gems_optim_config")
