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
from dataclasses import dataclass

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.event import listens_for
from sqlalchemy.orm import sessionmaker

from antarest.core.utils.fastapi_sqlalchemy import db


@dataclass
class EventCounter:
    transaction_start: int = 0
    transaction_end: int = 0
    begin: int = 0
    rollback: int = 0
    commit: int = 0


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:")
    return sessionmaker(bind=engine)


@pytest.fixture
def events_counter(session_factory):
    counter = EventCounter()

    @listens_for(session_factory, "after_begin")
    def after_begin(session, transaction, connection):
        counter.begin = counter.begin + 1

    @listens_for(session_factory, "after_rollback")
    def after_rollback(session):
        counter.rollback = counter.rollback + 1

    @listens_for(session_factory, "after_commit")
    def after_commit(session):
        counter.commit = counter.commit + 1

    @listens_for(session_factory, "after_transaction_create")
    def on_transaction_start(session, transaction):
        counter.transaction_start = counter.transaction_start + 1

    @listens_for(session_factory, "after_transaction_end")
    def on_transaction_end(session, transaction):
        counter.transaction_end = counter.transaction_end + 1

    return counter


def test_db_session_is_rollbacked_on_exit(session_factory, events_counter):
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
def test_db_session_is_rollbacked_on_exception(session_factory, events_counter, commit_on_exit):
    with db(session_factory):
        db.session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        assert events_counter.begin == 1
        assert events_counter.transaction_start == 1

    assert events_counter.transaction_end == 1
    assert events_counter.rollback == 1
    assert events_counter.commit == 0


def test_db_session_is_committed_on_autocommit(session_factory, events_counter):
    with db(session_factory, commit_on_exit=True):
        db.session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        assert events_counter.begin == 1
        assert events_counter.transaction_start == 1

    assert events_counter.transaction_end == 1
    assert events_counter.rollback == 0
    assert events_counter.commit == 1
