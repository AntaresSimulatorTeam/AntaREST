"""create_intermediate_table

Revision ID: 844f4a7cd371
Revises: 4121d3b48393
Create Date: 2026-05-28 16:27:08.165716

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '844f4a7cd371'
down_revision = '4121d3b48393'
branch_labels = None
depends_on = None


INTERMEDIATE_TABLE = 'study_data'

DAO_TABLES = [
    "area",
    "binding_constraint",
    "comments",
    "district",
    "layer",
    "scenario_binding_constraints",
    "general_config",
    "advanced_parameters",
    "adequacy_patch_parameters",
    "compatibility_parameters",
    "optimization_preferences",
    "timeseries_config",
    "playlist",
    "thematic_trimming",
    "user_resources",
    "xpansion_settings",
]

def _transform_tables(new_foreign_key: str, reference_table_name: str):
    """    
    SQLITE doesn't support dropping foreign key constraints, so we have to manually alter the tables
    """
    for table_name in DAO_TABLES:
        metadata = sa.MetaData()
        metadata.reflect(bind=op.get_bind(), only=[table_name])
        table = metadata.tables[table_name]

        # Collect all existing foreign key constraints
        existing_fk_constraints = []
        for fk in table.foreign_key_constraints:
            if fk.referred_table.name != reference_table_name:
                # Skip the foreign key we want to replace
                existing_fk_constraints.append(fk)

        # Generate the new foreign key constraint
        new_fk_constraint = sa.ForeignKeyConstraint(['study_id'],[new_foreign_key], name=f'fk_{table_name}_study_id', ondelete='CASCADE')
        existing_fk_constraints.append(new_fk_constraint)

        # Create a new table with the new foreign key constraint
        cols = [sa.Column(col.name, col.type, nullable=col.nullable, primary_key=col.primary_key, unique=col.unique) for col in table.columns]
        op.create_table(f"{table_name}_new", *cols, *existing_fk_constraints)

        # Drop the old table
        op.drop_table(table_name)

        # Rename the new table to the original name
        op.rename_table(f"{table_name}_new", table_name)

def upgrade():
    """
    Introduce an intermediate table between DAO and Study, useful for clearing variant snapshots.
    When doing so, we'll only have to flush this table and everything will be removed by cascade.
    """

    # Create the new intermediate table
    op.create_table(
        INTERMEDIATE_TABLE,
        sa.Column('study_id', sa.String(length=36), sa.ForeignKey('study.id', ondelete='CASCADE'), nullable=False, primary_key=True),
    )

    # For each DAO table that previously referenced study.id, we'll now use the intermediate table
    _transform_tables(f"{INTERMEDIATE_TABLE}.study_id", reference_table_name="study")

def downgrade():
    _transform_tables("study.id", reference_table_name=INTERMEDIATE_TABLE)

    op.drop_table(INTERMEDIATE_TABLE)
