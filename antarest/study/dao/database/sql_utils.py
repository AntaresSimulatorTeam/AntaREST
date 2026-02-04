# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
"""
Collection of SQL related utilities

"""

from typing import Any

from sqlalchemy import Column, Table, and_, insert, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql.dml import Insert as PgInsert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.sqlite.dml import Insert as SqliteInsert
from sqlalchemy.orm import Session


def generic_upsert_multiple(
    session: Session,
    table: Table,
    values: list[dict[str, Any]],
) -> None:
    """
    Upsert implementation which does not rely on a specific dialect.
    Note that it could fail on concurrency issues, since it relies on several sequential
    requests.

    Assumes all columns are updated.

    """
    if not values:
        return

    key_columns = _key_columns(table)
    update_columns = _update_columns(table)

    # First a select to identify existing rows
    def _key(vals: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(vals[column.name] for column in key_columns)

    key_tuples = [_key(row) for row in values]
    existing_stmt = select(*key_columns).where(tuple_(*key_columns).in_(key_tuples))
    existing_rows = session.execute(existing_stmt).fetchall()
    existing_keys = {tuple(getattr(row, column.name) for column in key_columns) for row in existing_rows}

    rows_to_insert: list[dict[str, Any]] = []
    rows_to_update: list[dict[str, Any]] = []
    for row in values:
        if _key(row) in existing_keys:
            rows_to_update.append(row)
        else:
            rows_to_insert.append(row)

    if rows_to_insert:
        session.execute(insert(table).values(rows_to_insert))

    # 1 query per update unfortunately. Might be possible to optimize, but not worth it for us now.
    for row in rows_to_update:
        filters = [column == row[column.name] for column in key_columns]
        stmt_update = update(table).where(and_(*filters)).values({k: row[k.name] for k in update_columns})
        session.execute(stmt_update)


def _key_columns(table: Table) -> list[Column[Any]]:
    return [column for column in table.columns.values() if column.primary_key]


def _update_columns(table: Table) -> list[Column[Any]]:
    return [column for column in table.columns.values() if not column.primary_key]


def upsert_one(
    session: Session,
    table: Table,
    values: dict[str, Any],
) -> None:
    return upsert_multiple(session, table, [values])


def upsert_multiple(
    session: Session,
    table: Table,
    values: list[dict[str, Any]],
) -> None:
    """
    Inserts or updates data into a database table. Optimizes for specific postgresql and sqlite dialects,
    and falls back on standard SQL otherwise.

    Assumes all columns are updated.
    """
    if not values:
        return

    dialect = session.get_bind().dialect.name
    if dialect in {"postgresql", "sqlite"}:
        key_columns = _key_columns(table)
        update_columns = _update_columns(table)

        # Note for the ignorant: the postgres and sqlite syntax requires to explicitly
        # state the list of columns that we want to update, hence the set_ clause
        stmt: PgInsert | SqliteInsert
        if dialect == "postgresql":
            stmt = pg_insert(table).values(values)
        else:
            stmt = sqlite_insert(table).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=key_columns,
            set_={column: getattr(stmt.excluded, column.name) for column in update_columns},
        )
        session.execute(stmt)
    else:
        generic_upsert_multiple(session, table, values)
