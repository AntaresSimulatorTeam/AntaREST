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
from pathlib import Path

import pytest
from sqlalchemy import Column, Engine, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.exc import CompileError
from sqlalchemy.orm import Session, sessionmaker

from antarest.study.dao.database.sql_utils import upsert_multiple, upsert_one
from tests.db_statement_recorder import DBStatementRecorder

METADATA = MetaData()

TEST_TABLE = Table(
    "test",
    METADATA,
    Column("id", String, primary_key=True, nullable=False),
    Column("sub_id", String, primary_key=True, nullable=False),
    Column("str_value", String, nullable=False),
    Column("int_value", Integer, nullable=False),
)


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    METADATA.create_all(engine)
    return engine


@pytest.fixture
def session(engine: Engine) -> Session:
    return sessionmaker(bind=engine)()


def test_upsert_multiple(engine: Engine, session: Session) -> None:
    with DBStatementRecorder(engine) as db_recorder:
        insertions = [
            {"id": "1", "sub_id": "2", "str_value": "val1", "int_value": 12},
            {"id": "1", "sub_id": "3", "str_value": "val2", "int_value": 52},
            {"id": "2", "sub_id": "3", "str_value": "val3", "int_value": 66},
        ]
        upsert_multiple(session, TEST_TABLE, values=insertions)
        assert len(db_recorder.sql_statements) == 1

    rows = session.execute(select(TEST_TABLE)).fetchall()
    assert rows == [("1", "2", "val1", 12), ("1", "3", "val2", 52), ("2", "3", "val3", 66)]

    # Updates one existing row and inserts a new one
    with DBStatementRecorder(engine) as db_recorder:
        updates = [
            {"id": "1", "sub_id": "2", "str_value": "val1_updated", "int_value": 72},
            {"id": "3", "sub_id": "4", "str_value": "val4", "int_value": 0},
        ]
        upsert_multiple(
            session,
            TEST_TABLE,
            values=updates,
        )
        assert len(db_recorder.sql_statements) == 1

    rows = session.execute(select(TEST_TABLE)).fetchall()
    assert rows == [
        ("1", "2", "val1_updated", 72),
        ("1", "3", "val2", 52),
        ("2", "3", "val3", 66),
        ("3", "4", "val4", 0),
    ]


def test_upsert_multiple_missing_key_raises(session: Session) -> None:
    insertions = [
        {"id": "1", "sub_id": "1", "str_value": "val2", "int_value": 52},
        {"id": "1", "sub_id": "3", "str_value": "val2"},
        {"id": "2", "sub_id": "3", "str_value": "val3", "int_value": 66},
    ]
    with pytest.raises(CompileError):
        upsert_multiple(session, TEST_TABLE, values=insertions)


def test_upsert_one(session: Session) -> None:
    # Inserting one row
    upsert_one(session, TEST_TABLE, values={"id": "1", "sub_id": "1", "str_value": "val1", "int_value": 1})
    rows = session.execute(select(TEST_TABLE)).fetchall()
    assert rows == [("1", "1", "val1", 1)]

    # Inserting one different row
    upsert_one(session, TEST_TABLE, values={"id": "2", "sub_id": "2", "str_value": "val2", "int_value": 2})
    rows = session.execute(select(TEST_TABLE)).fetchall()
    assert rows == [("1", "1", "val1", 1), ("2", "2", "val2", 2)]

    # Updating an existing row
    upsert_one(session, TEST_TABLE, values={"id": "1", "sub_id": "1", "str_value": "val3", "int_value": 3})
    rows = session.execute(select(TEST_TABLE)).fetchall()
    assert rows == [("1", "1", "val3", 3), ("2", "2", "val2", 2)]


def test_upsert_with_too_many_lines(engine: Engine, session: Session) -> None:
    """
    SQL seems to have a limit of 2¹⁵ values to upsert at a time.
    When trying to insert more than 2¹⁵ values, the `upsert_multiple` function should split the data in chunks to
    avoid raising an error.
    """
    values = [{"id": str(k), "sub_id": str(k), "str_value": "val1", "int_value": 1} for k in range(8200)]

    with DBStatementRecorder(engine) as db_recorder:
        upsert_multiple(session, TEST_TABLE, values=values)
        assert len(db_recorder.sql_statements) == 2  # We split the data in 2 batches
