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

from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session, sessionmaker


@dataclass
class DbEventCounter:
    transaction_start: int = 0
    transaction_end: int = 0
    begin: int = 0
    rollback: int = 0
    commit: int = 0


def create_db_event_counter(session_factory: sessionmaker[Session]) -> DbEventCounter:
    counter = DbEventCounter()

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
