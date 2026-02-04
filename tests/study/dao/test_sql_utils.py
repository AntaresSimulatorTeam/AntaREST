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
from typing import Callable

import pytest
from db_statement_recorder import DBStatementRecorder
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.orm import sessionmaker

from antarest.study.dao.database.sql_utils import generic_upsert_multiple, upsert_multiple

METADATA = MetaData()

TEST_TABLE = Table(
    "test",
    METADATA,
    Column("id", String, primary_key=True),
    Column("sub_id", String, primary_key=True),
    Column("str_value", String),
    Column("int_value", Integer),
)


@pytest.mark.parametrize(
    "upsert_method, expected_queries_1, expected_queries_2", [(generic_upsert_multiple, 2, 3), (upsert_multiple, 1, 1)]
)
def test_upsert_multiple(tmp_path: Path, upsert_method: Callable, expected_queries_1: int, expected_queries_2: int):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")

    METADATA.create_all(engine)

    sessionfactory = sessionmaker(bind=engine)
    session = sessionfactory()

    with DBStatementRecorder(engine) as db_recorder:
        insertions = [
            {"id": "1", "sub_id": "2", "str_value": "val1", "int_value": 12},
            {"id": "1", "sub_id": "3", "str_value": "val2", "int_value": 52},
            {"id": "2", "sub_id": "3", "str_value": "val3", "int_value": 66},
        ]
        upsert_method(session, TEST_TABLE, values=insertions)
        assert len(db_recorder.sql_statements) == expected_queries_1

    rows = session.execute(select(TEST_TABLE)).fetchall()
    assert rows == [("1", "2", "val1", 12), ("1", "3", "val2", 52), ("2", "3", "val3", 66)]

    # Updates one existing row and inserts a new one
    with DBStatementRecorder(engine) as db_recorder:
        updates = [
            {"id": "1", "sub_id": "2", "str_value": "val1_updated", "int_value": 72},
            {"id": "3", "sub_id": "4", "str_value": "val4", "int_value": 0},
        ]
        upsert_method(
            session,
            TEST_TABLE,
            values=updates,
        )
        assert len(db_recorder.sql_statements) == expected_queries_2

    rows = session.execute(select(TEST_TABLE)).fetchall()
    assert rows == [
        ("1", "2", "val1_updated", 72),
        ("1", "3", "val2", 52),
        ("2", "3", "val3", 66),
        ("3", "4", "val4", 0),
    ]
