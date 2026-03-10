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

from sqlalchemy import Column, Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql.dml import Insert as PgInsert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.sqlite.dml import Insert as SqliteInsert
from sqlalchemy.orm import Session


def _key_columns(table: Table) -> list[Column[Any]]:
    """
    Returns columns that are part of the primary key.
    """
    return [column for column in table.columns.values() if column.primary_key]


def _update_columns(table: Table) -> list[Column[Any]]:
    """
    Returns columns that are not part of the primary key, which will all be assumed updated.
    """
    return [column for column in table.columns.values() if not column.primary_key]


def upsert_one(
    session: Session,
    table: Table,
    values: dict[str, Any],
) -> None:
    """
    Updates or inserts a single row.

    Notes:
        Assumes:
         - all columns are updated
         - value dictionary has the correct columns: we don't check for this
    """
    upsert_multiple(session, table, [values])


def upsert_multiple(
    session: Session,
    table: Table,
    values: list[dict[str, Any]],
) -> None:
    """
    Inserts or updates data into a database table. Optimizes for specific postgresql and sqlite dialects,
    and falls back on standard SQL otherwise.

    Notes:
        Assumes:
         - all columns are updated
         - value dictionaries all have the correct columns: we don't check for this
    """
    if not values:
        return

    prototype_value = values[0]

    dialect = session.get_bind().dialect.name
    if dialect in {"postgresql", "sqlite"}:
        key_columns = _key_columns(table)
        update_columns = [c for c in _update_columns(table) if c.name in prototype_value]

        # Note: the postgres and sqlite syntax requires to explicitly
        # state the list of columns that we want to update, hence the set_ clause.
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
        raise NotImplementedError(f"Dialect {dialect} not supported")
