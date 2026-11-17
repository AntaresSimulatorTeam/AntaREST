"""split_gems_components_table

Revision ID: 1c8b0b189035
Revises: b8e5c1a7d902
Create Date: 2026-11-12 16:40:14.326526

"""
from alembic import op
import sqlalchemy as sa

from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = '1c8b0b189035'
down_revision = 'b8e5c1a7d902'
branch_labels = None
depends_on = None


def upgrade():
    variables_type_enum = sa.Enum("continuous", "integer", "binary", name="variablestype")

    with op.batch_alter_table("gems_models", schema=None) as batch_op:
        batch_op.drop_column("variables")
        batch_op.drop_column("constraints")
        batch_op.drop_column("objective_contributions")

    op.create_table(
        "gems_models_variables",
        study_data_id_col(primary_key=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("type", variables_type_enum, nullable=False),
        sa.Column("lower_bound", sa.String(), nullable=True),
        sa.Column("upper_bound", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("study_data_id", "library_id", "model_id", "id", name="pk_gems_model_variables"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id"],
            ["gems_models.study_data_id", "gems_models.library_id", "gems_models.id"],
            name=op.f("fk_gems_model_variables"),
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "gems_models_constraints",
        study_data_id_col(primary_key=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("expression", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("study_data_id", "library_id", "model_id", "id", name="pk_gems_model_constraints"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id"],
            ["gems_models.study_data_id", "gems_models.library_id", "gems_models.id"],
            name=op.f("fk_gems_model_constraints"),
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "gems_models_objective_contributions",
        study_data_id_col(primary_key=False),
        sa.Column("library_id", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("expression", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("study_data_id", "library_id", "model_id", "id", name="pk_gems_model_objective_contributions"),
        sa.ForeignKeyConstraint(
            ["study_data_id", "library_id", "model_id"],
            ["gems_models.study_data_id", "gems_models.library_id", "gems_models.id"],
            name=op.f("fk_gems_model_objective_contributions"),
            ondelete="CASCADE",
        ),
    )


def downgrade():
    with op.batch_alter_table("gems_models", schema=None) as batch_op:
        batch_op.add_column(sa.Column("variables", sa.String(), nullable=False))
        batch_op.add_column(sa.Column("constraints", sa.String(), nullable=False))
        batch_op.add_column(sa.Column("objective_contributions", sa.String(), nullable=False))

    op.drop_table("gems_models_variables")
    op.drop_table("gems_models_constraints")
    op.drop_table("gems_models_objective_contributions")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="variablestype").drop(bind, checkfirst=True)