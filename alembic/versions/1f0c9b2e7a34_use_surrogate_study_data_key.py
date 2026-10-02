"""use_surrogate_study_data_key

Replace the 36 chars `study_id` carried by every study data table with the bigint surrogate
key `study_data.study_data_id`.

Revision ID: 1f0c9b2e7a34
Revises: 6012b0407e38
Create Date: 2026-08-11 09:00:00.000000

"""

import hashlib
import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "1f0c9b2e7a34"
down_revision = "6012b0407e38"
branch_labels = None
depends_on = None


logger = logging.getLogger("alembic.runtime.migration")

REFERENCE_TABLE = "study_data"
STRING_KEY = "study_id"
STRING_KEY_TYPE = sa.String(36)
SURROGATE_KEY = "study_data_id"
# `BigInteger` alone does not autoincrement on SQLite: only `INTEGER PRIMARY KEY` aliases the rowid.
SURROGATE_KEY_TYPE = sa.BigInteger().with_variant(sa.Integer, "sqlite")

# PostgreSQL silently truncates identifiers beyond this length, which could make two generated
# names collide.
MAX_IDENTIFIER_LENGTH = 63


def _identifier(*parts: str) -> str:
    """
    Build a deterministic constraint name, short enough for PostgreSQL to keep it unique.
    """
    name = "_".join(parts)
    if len(name) <= MAX_IDENTIFIER_LENGTH:
        return name
    digest = hashlib.md5(name.encode()).hexdigest()[:8]
    return f"{name[: MAX_IDENTIFIER_LENGTH - 9]}_{digest}"


def _quoted(identifier: str) -> str:
    return f'"{identifier}"'


def _swap(columns: Sequence[str], source: str, target: str) -> List[str]:
    return [target if column == source else column for column in columns]


def _key_column(name: str, *, nullable: bool) -> "sa.Column[Any]":
    column_type = SURROGATE_KEY_TYPE if name == SURROGATE_KEY else STRING_KEY_TYPE
    return sa.Column(name, column_type, nullable=nullable)


def _data_tables(foreign_keys: Dict[str, List[Any]], key: str) -> List[str]:
    """
    All tables transitively keyed on `study_data` through `key`, parents before children.

    The set is discovered rather than hard-coded so that this migration keeps describing the
    schema as it stands at this revision, whatever the models become later on.
    """
    known = {REFERENCE_TABLE}
    frontier = {REFERENCE_TABLE}
    while frontier:
        frontier = {
            table
            for table, fks in foreign_keys.items()
            if table not in known
            and any(fk["referred_table"] in known and key in fk["constrained_columns"] for fk in fks)
        }
        known |= frontier
    known.discard(REFERENCE_TABLE)

    # Topological sort: a table is emitted once every data table it references is emitted.
    # Self-references (`user_resources.parent_id`) are not a real dependency.
    pending = {
        table: {fk["referred_table"] for fk in foreign_keys[table] if fk["referred_table"] in known} - {table}
        for table in known
    }
    ordered: List[str] = []
    while pending:
        ready = sorted(table for table, parents in pending.items() if not parents - set(ordered))
        if not ready:
            raise RuntimeError(f"Cyclic foreign keys between study data tables: {sorted(pending)}")
        ordered.extend(ready)
        for table in ready:
            del pending[table]
    return ordered


class _Snapshot:
    """
    Reflection taken once, before any DDL is emitted: an inspector used while the schema is being
    rewritten would return a mix of old and new definitions.
    """

    def __init__(self, key: str) -> None:
        inspector = sa.inspect(op.get_bind())
        self.foreign_keys: Dict[str, List[Any]] = {
            table: list(inspector.get_foreign_keys(table)) for table in inspector.get_table_names()
        }
        self.tables = _data_tables(self.foreign_keys, key)
        self.primary_keys: Dict[str, List[str]] = {}
        # SQLite leaves primary key constraints unnamed; only the PostgreSQL path needs the names.
        self.primary_key_names: Dict[str, Optional[str]] = {}
        for table in [REFERENCE_TABLE, *self.tables]:
            primary_key = inspector.get_pk_constraint(table)
            self.primary_keys[table] = list(primary_key["constrained_columns"])
            self.primary_key_names[table] = primary_key["name"]
        # Tables whose study key column is rewritten, hence whose foreign keys must be retargeted.
        self.referenced: Set[str] = {REFERENCE_TABLE, *self.tables}

    def key_foreign_keys(self, table: str, key: str) -> List[Any]:
        """
        Foreign keys of `table` built on the study key, i.e. all of them but the self-reference
        of `user_resources.parent_id`.
        """
        return [fk for fk in self.foreign_keys[table] if key in fk["constrained_columns"]]


def _drop_key_foreign_keys(snapshot: _Snapshot, key: str) -> None:
    """
    Every foreign key on the study key must go before the primary keys they depend on.
    """
    for table in snapshot.tables:
        for fk in snapshot.key_foreign_keys(table, key):
            op.drop_constraint(fk["name"], table, type_="foreignkey")


def _primary_key_name(snapshot: _Snapshot, table: str) -> str:
    name = snapshot.primary_key_names[table]
    if not name:
        raise RuntimeError(f"Table {table} has no named primary key constraint, it cannot be dropped")
    return name


def _swap_primary_keys(snapshot: _Snapshot, *, source: str, target: str) -> None:
    """
    Replace `source` by `target` in the primary key of the reference table and of every data table
    keyed on it, keeping it the leading column so that index coverage is preserved.
    """
    op.drop_constraint(_primary_key_name(snapshot, REFERENCE_TABLE), REFERENCE_TABLE, type_="primary")
    op.create_primary_key(_identifier(REFERENCE_TABLE, "pkey"), REFERENCE_TABLE, [target])

    for table in snapshot.tables:
        primary_key = snapshot.primary_keys[table]
        if source not in primary_key:
            continue
        op.drop_constraint(_primary_key_name(snapshot, table), table, type_="primary")
        op.create_primary_key(_identifier(table, "pkey"), table, _swap(primary_key, source, target))


def _create_foreign_keys(snapshot: _Snapshot, *, source: str, target: str) -> None:
    for table in snapshot.tables:
        for fk in snapshot.key_foreign_keys(table, source):
            local = _swap(fk["constrained_columns"], source, target)
            referred = _swap(fk["referred_columns"], source, target)
            op.create_foreign_key(
                _identifier("fk", table, *local),
                table,
                fk["referred_table"],
                local,
                referred,
                ondelete=fk["options"].get("ondelete"),
                onupdate=fk["options"].get("onupdate"),
            )


#
# PostgreSQL: constraints can be dropped and recreated, so tables stay in place.
#
# The new key column is therefore appended rather than kept in first position, which PostgreSQL
# cannot change without rewriting the table. Only its position in the primary key matters, and
# that one is preserved.
#


def _upgrade_postgresql(snapshot: _Snapshot) -> None:
    # `BIGSERIAL` creates the sequence and fills existing rows in a single statement.
    op.execute(sa.text(f'ALTER TABLE "{REFERENCE_TABLE}" ADD COLUMN {SURROGATE_KEY} BIGSERIAL'))
    op.create_unique_constraint(_identifier("uq", REFERENCE_TABLE, STRING_KEY), REFERENCE_TABLE, [STRING_KEY])

    for table in snapshot.tables:
        op.add_column(table, sa.Column(SURROGATE_KEY, sa.BigInteger(), nullable=True))
        op.execute(
            sa.text(
                f'UPDATE "{table}" SET {SURROGATE_KEY} = sd.{SURROGATE_KEY} '
                f'FROM "{REFERENCE_TABLE}" AS sd WHERE sd.{STRING_KEY} = "{table}".{STRING_KEY}'
            )
        )
        op.alter_column(table, SURROGATE_KEY, existing_type=sa.BigInteger(), nullable=False)

    _drop_key_foreign_keys(snapshot, STRING_KEY)
    _swap_primary_keys(snapshot, source=STRING_KEY, target=SURROGATE_KEY)

    for table in snapshot.tables:
        # The snapshot predates the DDL above, so the primary key is tested on the column the
        # surrogate key took the place of.
        if STRING_KEY not in snapshot.primary_keys[table]:
            # Not covered by the primary key: neither PostgreSQL nor SQLite indexes foreign keys.
            op.create_index(_identifier("ix", table, SURROGATE_KEY), table, [SURROGATE_KEY])
        op.drop_column(table, STRING_KEY)

    _create_foreign_keys(snapshot, source=STRING_KEY, target=SURROGATE_KEY)


def _downgrade_postgresql(snapshot: _Snapshot) -> None:
    for table in reversed(snapshot.tables):
        op.execute(sa.text(f'DELETE FROM "{table}"'))

    _drop_key_foreign_keys(snapshot, SURROGATE_KEY)
    for table in snapshot.tables:
        # The tables are empty, so the column can be added `NOT NULL` right away.
        op.add_column(table, _key_column(STRING_KEY, nullable=False))

    _swap_primary_keys(snapshot, source=SURROGATE_KEY, target=STRING_KEY)

    op.drop_constraint(_identifier("uq", REFERENCE_TABLE, STRING_KEY), REFERENCE_TABLE, type_="unique")
    # The owned `BIGSERIAL` sequence goes away with the column, as do the indexes on the data tables.
    op.drop_column(REFERENCE_TABLE, SURROGATE_KEY)
    for table in snapshot.tables:
        op.drop_column(table, SURROGATE_KEY)

    _create_foreign_keys(snapshot, source=SURROGATE_KEY, target=STRING_KEY)


#
# SQLite: foreign keys cannot be dropped, so every table is rebuilt.
#


def _upgrade_sqlite(snapshot: _Snapshot) -> None:
    metadata = sa.MetaData()
    metadata.reflect(bind=op.get_bind(), only=[*snapshot.tables])

    # The reference table goes first: the data tables read their new key from it.
    op.create_table(
        f"{REFERENCE_TABLE}_new",
        sa.Column(SURROGATE_KEY, SURROGATE_KEY_TYPE, primary_key=True, autoincrement=True),
        sa.Column(STRING_KEY, STRING_KEY_TYPE, nullable=False, unique=True),
        sa.ForeignKeyConstraint(
            [STRING_KEY], ["study.id"], name=_identifier("fk", REFERENCE_TABLE, STRING_KEY), ondelete="CASCADE"
        ),
    )
    op.execute(
        sa.text(f'INSERT INTO "{REFERENCE_TABLE}_new" ({STRING_KEY}) SELECT {STRING_KEY} FROM "{REFERENCE_TABLE}"')
    )
    op.drop_table(REFERENCE_TABLE)
    op.rename_table(f"{REFERENCE_TABLE}_new", REFERENCE_TABLE)

    for table in snapshot.tables:
        _rebuild_sqlite_table(
            metadata.tables[table],
            snapshot,
            source=STRING_KEY,
            target=SURROGATE_KEY,
            copy_data=True,
            index_key=True,
        )


def _downgrade_sqlite(snapshot: _Snapshot) -> None:
    metadata = sa.MetaData()
    metadata.reflect(bind=op.get_bind(), only=[*snapshot.tables])

    op.create_table(
        f"{REFERENCE_TABLE}_new",
        sa.Column(STRING_KEY, STRING_KEY_TYPE, primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(
            [STRING_KEY], ["study.id"], name=_identifier("fk", REFERENCE_TABLE, STRING_KEY), ondelete="CASCADE"
        ),
    )
    op.execute(
        sa.text(f'INSERT INTO "{REFERENCE_TABLE}_new" ({STRING_KEY}) SELECT {STRING_KEY} FROM "{REFERENCE_TABLE}"')
    )
    op.drop_table(REFERENCE_TABLE)
    op.rename_table(f"{REFERENCE_TABLE}_new", REFERENCE_TABLE)

    for table in snapshot.tables:
        _rebuild_sqlite_table(
            metadata.tables[table],
            snapshot,
            source=SURROGATE_KEY,
            target=STRING_KEY,
            copy_data=False,
            index_key=False,
        )


def _rebuild_sqlite_table(
    table: sa.Table,
    snapshot: _Snapshot,
    *,
    source: str,
    target: str,
    copy_data: bool,
    index_key: bool,
) -> None:
    """
    Recreate `table` in place with `source` replaced by `target`, in the same column position.

    When `copy_data` is set, rows are carried over and the new key is read from the reference
    table, which must already expose both columns. `index_key` adds an explicit index on the new
    key for the tables that do not carry it in their primary key.
    """
    name = table.name
    columns = [
        _key_column(target, nullable=False) if column.name == source else _copied_column(column)
        for column in table.columns
    ]
    primary_key = snapshot.primary_keys[name]
    op.create_table(
        f"{name}_new",
        *columns,
        sa.PrimaryKeyConstraint(*_swap(primary_key, source, target), name=_identifier(name, "pkey")),
        *_rebuilt_foreign_keys(table, snapshot, source=source, target=target),
    )

    if copy_data:
        # Column names are quoted: some of them (`group`, `order`) are SQL keywords.
        inserted = [_quoted(column.name) for column in columns]
        selected = [
            f"sd.{target}" if column.name == target else f"{_quoted(name)}.{_quoted(column.name)}" for column in columns
        ]
        op.execute(
            sa.text(
                f"INSERT INTO {_quoted(f'{name}_new')} ({', '.join(inserted)}) "
                f"SELECT {', '.join(selected)} "
                f"FROM {_quoted(name)} JOIN {_quoted(REFERENCE_TABLE)} AS sd "
                f"ON sd.{source} = {_quoted(name)}.{source}"
            )
        )

    op.drop_table(name)
    op.rename_table(f"{name}_new", name)

    # `primary_key` is the one reflected before the rebuild, hence tested on `source`.
    if index_key and source not in primary_key:
        op.create_index(_identifier("ix", name, target), name, [target])


def _copied_column(column: "sa.Column[Any]") -> "sa.Column[Any]":
    return sa.Column(
        column.name,
        column.type,
        nullable=column.nullable,
        server_default=column.server_default,
    )


def _rebuilt_foreign_keys(
    table: sa.Table, snapshot: _Snapshot, *, source: str, target: str
) -> List[sa.ForeignKeyConstraint]:
    constraints = []
    for constraint in table.foreign_key_constraints:
        local = []
        referred_table = ""
        referred = []
        for element in constraint.elements:
            local.append(element.parent.name)
            referred_table, referred_column = element.target_fullname.rsplit(".", 1)
            referred.append(referred_column)
        if referred_table in snapshot.referenced:
            referred = _swap(referred, source, target)
        local = _swap(local, source, target)
        constraints.append(
            sa.ForeignKeyConstraint(
                local,
                [f"{referred_table}.{column}" for column in referred],
                name=_identifier("fk", table.name, *local),
                ondelete=constraint.ondelete,
                onupdate=constraint.onupdate,
            )
        )
    return constraints


def _run(postgresql: Callable[[_Snapshot], None], sqlite: Callable[[_Snapshot], None], *, key: str) -> None:
    snapshot = _Snapshot(key)
    dialect_name = op.get_context().dialect.name
    if dialect_name == "sqlite":
        sqlite(snapshot)
    elif dialect_name == "postgresql":
        postgresql(snapshot)
    else:
        raise NotImplementedError(
            f"Unsupported database dialect '{dialect_name}'. Only sqlite and postgresql are supported."
        )


def upgrade() -> None:
    _run(_upgrade_postgresql, _upgrade_sqlite, key=STRING_KEY)


def downgrade() -> None:
    logger.warning(
        "Downgrading %s: every table storing study data in the database is rebuilt empty. "
        "All database-stored study content (areas, clusters, settings, matrix references) is lost. "
        "The studies themselves are preserved.",
        revision,
    )
    _run(_downgrade_postgresql, _downgrade_sqlite, key=SURROGATE_KEY)
