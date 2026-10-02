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

from enum import Enum as PyEnum
from typing import Any, Type

from sqlalchemy import Column, Enum, Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql.dml import Insert as PgInsert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.sqlite.dml import Insert as SqliteInsert
from sqlalchemy.orm import Session


def enum_col(enum_class: Type[PyEnum], **kwargs: Any) -> Enum:
    """
    Create a SQLAlchemy Enum type that uses enum values (not names).

    PostgreSQL enums are case-sensitive. Since our Python enums use values
    (e.g. "Economy") that differ from names (e.g. "ECONOMY"), this helper
    ensures the DB enum type is built from values, matching the migration.
    """
    return Enum(enum_class, values_callable=lambda x: [e.value for e in x], **kwargs)


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

    dialect = session.get_bind().dialect.name
    if dialect not in {"postgresql", "sqlite"}:
        raise NotImplementedError(f"Dialect {dialect} not supported")

    # SQL seems to have a limit of 2¹⁵ parameters to give inside a single insert statement
    # If we have too many values, we need to split them in multiple insert statements
    max_insert_size = 2**15 - 1
    batch_size = max_insert_size // len(table.columns)
    batches = [values[i : i + batch_size] for i in range(0, len(values), batch_size)]

    key_columns = _key_columns(table)
    prototype_value = batches[0][0]
    update_columns = [c for c in _update_columns(table) if c.name in prototype_value]

    for batch in batches:
        # Note: the postgres and sqlite syntax requires to explicitly
        # state the list of columns that we want to update, hence the set_ clause.
        stmt: PgInsert | SqliteInsert
        if dialect == "postgresql":
            stmt = pg_insert(table).values(batch)
        else:
            stmt = sqlite_insert(table).values(batch)

        stmt = stmt.on_conflict_do_update(
            index_elements=key_columns,
            set_={column: getattr(stmt.excluded, column.name) for column in update_columns},
        )

        session.execute(stmt)
