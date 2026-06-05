"""create_intermediate_table

Revision ID: 844f4a7cd371
Revises: 4121d3b48393
Create Date: 2026-05-28 16:27:08.165716

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "844f4a7cd371"
down_revision = "4121d3b48393"
branch_labels = None
depends_on = None


INTERMEDIATE_TABLE = "study_data"

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


def _find_study_id_fk(table_name: str, reference_table_name: str) -> dict[str, object]:
    foreign_keys = sa.inspect(op.get_bind()).get_foreign_keys(table_name)
    matching_fks = [
        fk
        for fk in foreign_keys
        if fk["constrained_columns"] == ["study_id"] and fk["referred_table"] == reference_table_name
    ]
    if len(matching_fks) != 1:
        raise RuntimeError(
            f"Expected exactly one foreign key from {table_name}.study_id to {reference_table_name}, "
            f"found {len(matching_fks)}"
        )
    return matching_fks[0]


def _get_ondelete(fk: dict[str, object]) -> str | None:
    options = fk.get("options") or {}
    assert isinstance(options, dict)
    ondelete = options.get("ondelete")
    if isinstance(ondelete, str):
        return ondelete
    return None


def _transform_tables_postgresql(new_reference_table: str, old_reference_table: str) -> None:
    """
    PostgreSQL can drop and recreate foreign key constraints directly, so keep existing tables in place.
    """
    for table_name in DAO_TABLES:
        fk = _find_study_id_fk(table_name, old_reference_table)
        fk_name = fk["name"]
        if not isinstance(fk_name, str) or not fk_name:
            raise RuntimeError(f"Foreign key from {table_name}.study_id to {old_reference_table} has no name")

        ondelete = _get_ondelete(fk)
        if ondelete != "CASCADE":
            print(f"Foreign key {fk_name} on {table_name}.study_id has ondelete={ondelete!r}")

        new_fk_name = f"fk_{table_name}_study_id"
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.drop_constraint(fk_name, type_="foreignkey")
            batch_op.create_foreign_key(
                new_fk_name,
                new_reference_table,
                ["study_id"],
                ["study_id" if new_reference_table == INTERMEDIATE_TABLE else "id"],
                ondelete=ondelete,
            )


def _transform_tables_sqlite(new_foreign_key: str, reference_table_name: str):
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
        new_fk_constraint = sa.ForeignKeyConstraint(
            ["study_id"], [new_foreign_key], name=f"fk_{table_name}_study_id", ondelete="CASCADE"
        )
        existing_fk_constraints.append(new_fk_constraint)

        # Create a new table with the new foreign key constraint
        cols = [
            sa.Column(col.name, col.type, nullable=col.nullable, primary_key=col.primary_key, unique=col.unique)
            for col in table.columns
        ]
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
        sa.Column(
            "study_id",
            sa.String(length=36),
            sa.ForeignKey("study.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
    )
    op.execute(sa.text(f"INSERT INTO {INTERMEDIATE_TABLE} (study_id) SELECT id FROM study"))

    # For each DAO table that previously referenced study.id, we'll now use the intermediate table
    dialect_name = op.get_context().dialect.name
    if dialect_name == "sqlite":
        _transform_tables_sqlite(f"{INTERMEDIATE_TABLE}.study_id", reference_table_name="study")
    elif dialect_name == "postgresql":
        _transform_tables_postgresql(new_reference_table=INTERMEDIATE_TABLE, old_reference_table="study")
    else:
        raise NotImplementedError(
            f"Unsupported database dialect '{dialect_name}'. Only sqlite and postgresql are supported."
        )


def downgrade():
    dialect_name = op.get_context().dialect.name
    if dialect_name == "sqlite":
        _transform_tables_sqlite("study.id", reference_table_name=INTERMEDIATE_TABLE)
    elif dialect_name == "postgresql":
        _transform_tables_postgresql(new_reference_table="study", old_reference_table=INTERMEDIATE_TABLE)
    else:
        raise NotImplementedError(
            f"Unsupported database dialect '{dialect_name}'. Only sqlite and postgresql are supported."
        )

    op.drop_table(INTERMEDIATE_TABLE)
