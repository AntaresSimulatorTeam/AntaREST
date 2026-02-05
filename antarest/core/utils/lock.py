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
Distributed lock implementations.

This module provides lock mechanisms for coordinating between multiple processes or workers.
It defines an abstract interface and concrete implementations for different backends.
"""

import logging
import threading
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Dict, Optional, Type

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing_extensions import override

logger = logging.getLogger(__name__)


class LockNotAcquired(Exception):
    """Raised when the lock could not be acquired (another process holds it)."""

    pass


class PostgresqlLockNotSupported(Exception):
    """Raised when trying to use PostgreSQL advisory locks on a non-PostgreSQL database."""

    pass


class DistributedLock(ABC):
    """
    Abstract base class for distributed locks.

    Implementations must be usable as context managers and should raise
    LockNotAcquired if the lock cannot be obtained when blocking=False.
    """

    @abstractmethod
    def __enter__(self) -> "DistributedLock":
        pass

    @abstractmethod
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        pass


class PostgresqlLock(DistributedLock):
    """
    PostgreSQL advisory lock implementation.

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
        LockNotAcquired: If blocking=False and the lock is already held
    """

    def __init__(self, session: Session, *, lock_id: int, blocking: bool = False) -> None:
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

    @override
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
                raise LockNotAcquired(
                    f"Could not acquire advisory lock {self._lock_id}. Another process is probably holding it."
                )

        logger.debug(f"Advisory lock {self._lock_id} acquired successfully")
        return self

    @override
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


class ThreadLock(DistributedLock):
    """
    Simple thread-based lock implementation for testing and single-process environments.

    This implementation uses threading.Lock and is suitable for:
    - Unit tests (no database required)
    - Development with SQLite
    - Single-process deployments

    Note: This lock only works within a single process. For multi-process
    coordination, use PostgresqlLock instead.

    Args:
        session: Ignored, accepted for API compatibility with PostgresqlLock
        lock_id: Unique identifier for this lock
        blocking: If True, wait for lock. If False (default), fail immediately if lock is held.
    """

    # Class-level registry of locks by ID (shared across all instances)
    _locks: Dict[int, threading.Lock] = {}
    _registry_lock = threading.Lock()

    def __init__(self, session: Optional[Session] = None, *, lock_id: int, blocking: bool = False) -> None:
        # session is ignored - accepted for API compatibility with PostgresqlLock
        self._lock_id = lock_id
        self._blocking = blocking
        self._lock_acquired = False

        # Get or create a lock for this ID
        with ThreadLock._registry_lock:
            if lock_id not in ThreadLock._locks:
                ThreadLock._locks[lock_id] = threading.Lock()
        self._lock = ThreadLock._locks[lock_id]

    @override
    def __enter__(self) -> "ThreadLock":
        logger.debug(f"Trying to acquire thread lock {self._lock_id}")
        self._lock_acquired = self._lock.acquire(blocking=self._blocking)

        if not self._lock_acquired:
            raise LockNotAcquired(
                f"Could not acquire thread lock {self._lock_id}. Another thread is probably holding it."
            )

        logger.debug(f"Thread lock {self._lock_id} acquired successfully")
        return self

    @override
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._lock_acquired:
            logger.debug(f"Releasing thread lock {self._lock_id}")
            self._lock.release()
            self._lock_acquired = False


def create_lock(session: Session, lock_id: int, blocking: bool = False) -> DistributedLock:
    """
    Factory function to create the appropriate lock implementation based on the database dialect.

    This function automatically detects the database dialect and returns:
    - PostgresqlLock for PostgreSQL databases (true distributed locking)
    - ThreadLock for other databases like SQLite (single-process locking)

    Usage:
        with db():
            with create_lock(db.session, lock_id=1001):
                do_something()

    Args:
        session: SQLAlchemy session to use for dialect detection
        lock_id: Unique integer identifier for this lock
        blocking: If True, wait for lock. If False (default), fail immediately if lock is held.

    Returns:
        A DistributedLock instance appropriate for the current database.
    """
    dialect_name = session.bind.dialect.name if session.bind else None

    if dialect_name == "postgresql":
        logger.debug(f"Using PostgresqlLock for lock_id={lock_id}")
        return PostgresqlLock(session, lock_id=lock_id, blocking=blocking)
    else:
        logger.debug(f"Using ThreadLock for lock_id={lock_id} (dialect: {dialect_name})")
        return ThreadLock(session, lock_id=lock_id, blocking=blocking)
