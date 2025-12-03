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
PostgreSQL advisory lock implementation.

Advisory locks are application-level locks that can be used to coordinate
between multiple processes or workers without locking actual database rows.
"""

import logging
from types import TracebackType
from typing import Optional, Type

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PostgresqlLockNotSupported(Exception):
    """Raised when trying to use PostgreSQL advisory locks on a non-PostgreSQL database."""

    pass


class PostgresqlLockNotAcquired(Exception):
    """Raised when the advisory lock could not be acquired (another process holds it)."""

    pass


class PostgresqlLock:
    """
    Context manager for PostgreSQL advisory locks.

    Advisory locks are useful for coordinating between multiple workers/processes
    without locking actual database rows. They are automatically released when
    the session ends.

    Usage:
        with db():
            with PostgresqlLock(db.session, lock_id=1001):
                do_something()

    Args:
        session: SQLAlchemy session to use for the lock
        lock_id: Unique integer identifier for this lock (application-defined)
        blocking: If True, wait for lock. If False (default), fail immediately if lock is held.

    Raises:
        PostgresqlLockNotSupported: If the database is not PostgreSQL
        PostgresqlLockNotAcquired: If blocking=False and the lock is already held
    """

    def __init__(self, session: Session, lock_id: int, blocking: bool = False) -> None:
        self._session = session
        self._lock_id = lock_id
        self._blocking = blocking
        self._lock_acquired = False

    def _check_dialect(self) -> None:
        """Verify that we're using PostgreSQL."""
        dialect_name = self._session.bind.dialect.name if self._session.bind else None
        if dialect_name != "postgresql":
            raise PostgresqlLockNotSupported(
                f"PostgreSQL advisory locks are only supported on PostgreSQL databases. Current dialect: {dialect_name}"
            )

    def __enter__(self) -> "PostgresqlLock":
        self._check_dialect()

        if self._blocking:
            # pg_advisory_lock blocks until the lock is available
            logger.debug(f"Acquiring advisory lock {self._lock_id} (blocking)")
            self._session.execute(text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": self._lock_id})
            self._lock_acquired = True
        else:
            # pg_try_advisory_lock returns immediately with True/False
            logger.debug(f"Trying to acquire advisory lock {self._lock_id} (non-blocking)")
            result = self._session.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": self._lock_id})
            self._lock_acquired = bool(result.scalar())

            if not self._lock_acquired:
                raise PostgresqlLockNotAcquired(
                    f"Could not acquire advisory lock {self._lock_id}. Another process is probably holding it."
                )

        logger.debug(f"Advisory lock {self._lock_id} acquired successfully")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._lock_acquired:
            logger.debug(f"Releasing advisory lock {self._lock_id}")
            self._session.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": self._lock_id})
            self._lock_acquired = False
