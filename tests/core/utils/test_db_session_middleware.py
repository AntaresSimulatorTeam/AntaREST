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

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from antarest.core.utils.fastapi_sqlalchemy import db
from tests.test_helpers.db import DbEventCounter, create_db_event_counter


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite:///:memory:")
    return sessionmaker(bind=engine)


@pytest.fixture
def events_counter(session_factory: sessionmaker[Session]) -> DbEventCounter:
    return create_db_event_counter(session_factory)


def test_db_session_is_rollbacked_on_exit(
    session_factory: sessionmaker[Session], events_counter: DbEventCounter
) -> None:
    # it's important that transactions are rollbacked on exit, otherwise some
    # transactions can be seen as unclosed (in case an exception happens on close)

    with db(session_factory):
        db.session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        assert events_counter.begin == 1
        assert events_counter.transaction_start == 1

    assert events_counter.transaction_end == 1
    assert events_counter.rollback == 1
    assert events_counter.commit == 0


@pytest.mark.parametrize("commit_on_exit", [False, True])
def test_db_session_is_rollbacked_on_exception(
    session_factory: sessionmaker[Session], events_counter: DbEventCounter, commit_on_exit: bool
) -> None:
    with db(session_factory):
        db.session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        assert events_counter.begin == 1
        assert events_counter.transaction_start == 1

    assert events_counter.transaction_end == 1
    assert events_counter.rollback == 1
    assert events_counter.commit == 0


def test_db_session_is_committed_on_autocommit(
    session_factory: sessionmaker[Session], events_counter: DbEventCounter
) -> None:
    with db(session_factory, commit_on_exit=True):
        db.session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        assert events_counter.begin == 1
        assert events_counter.transaction_start == 1

    assert events_counter.transaction_end == 1
    assert events_counter.rollback == 0
    assert events_counter.commit == 1
