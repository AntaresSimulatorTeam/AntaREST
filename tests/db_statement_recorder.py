# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
Record SQL statements in memory to diagnose the queries performed by the application.
"""

import contextlib
import types
import typing as t

from sqlalchemy import event 
from sqlalchemy.engine import Connection, Engine 


class DBStatementRecorder(contextlib.AbstractContextManager):  # type: ignore
    """
    Record SQL statements in memory to diagnose the queries performed by the application.

    Usage::

        from tests.db_statement_logger import DBStatementRecorder

        db_session = ...
        with DBStatementRecorder(db_session.bind) as db_recorder:
            # Perform some SQL queries
            ...

        # Get the SQL statements
        sql_statements = db_recorder.sql_statements

    See [SqlAlchemy Events](https://docs.sqlalchemy.org/en/14/orm/session_events.html) for more details.
    """

    def __init__(self, db_engine: Engine) -> None:
        self.db_engine: Engine = db_engine
        self.sql_statements: t.List[str] = []

    def __enter__(self) -> "DBStatementRecorder":
        event.listen(self.db_engine, "before_cursor_execute", self.before_cursor_execute)
        return self

    def __exit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_val: t.Optional[BaseException],
        exc_tb: t.Optional[types.TracebackType],
    ) -> t.Optional[bool]:
        event.remove(self.db_engine, "before_cursor_execute", self.before_cursor_execute)
        return None if exc_type is None else False  # propagate exceptions if any.

    def before_cursor_execute(
        self,
        conn: Connection,
        cursor: t.Any,
        statement: str,
        parameters: t.Any,
        context: t.Any,
        executemany: bool,
    ) -> None:
        # note: add a breakpoint here to debug the SQL statements.
        self.sql_statements.append(statement)

    def __str__(self) -> str:
        """
        Return a string representation the SQL statements.
        """
        if self.sql_statements:
            return "Recorded SQL statements:\n" + "\n-------\n".join(self.sql_statements)
        return "No SQL statements recorded."
