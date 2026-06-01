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
Tests for SoftFileLock.

Each scenario spawns real child processes (via multiprocessing) so that
file-lock exclusion between OS-level processes is exercised, not just
between threads of a single process.
"""

import multiprocessing
from pathlib import Path

from antarest.core.utils.lock import AntarestFileLock, LockNotAcquired


class TestSoftFileLock:
    def test_concurrent_processes_same_lock_raises(self, tmp_path: Path) -> None:
        """Two processes competing for the same lock: the second one must raise LockNotAcquired."""
        lock_path = str(tmp_path / "shared.lock")

        held_event = multiprocessing.Event()
        release_event = multiprocessing.Event()
        result_queue: multiprocessing.Queue = multiprocessing.Queue()  # type: ignore[type-arg]

        holder = multiprocessing.Process(target=self._acquire_and_hold, args=(lock_path, held_event, release_event))
        holder.start()

        # Wait until the first process actually holds the lock
        held_event.wait(timeout=5)

        contender = multiprocessing.Process(target=self._try_acquire, args=(lock_path, result_queue))
        contender.start()
        contender.join(timeout=5)

        # Let the holder release its lock and clean up
        release_event.set()
        holder.join(timeout=5)

        assert not result_queue.empty(), "Contender process did not report a result"
        acquired = result_queue.get_nowait()
        assert acquired is False, "Second process should NOT have acquired the already-held lock"

    def test_sequential_processes_same_lock_succeed(self, tmp_path: Path) -> None:
        """Two processes acquiring the same lock one after the other must both succeed."""
        lock_path = str(tmp_path / "sequential.lock")
        result_queue: multiprocessing.Queue = multiprocessing.Queue()  # type: ignore[type-arg]

        first = multiprocessing.Process(target=self._try_acquire, args=(lock_path, result_queue))
        first.start()
        first.join(timeout=5)

        second = multiprocessing.Process(target=self._try_acquire, args=(lock_path, result_queue))
        second.start()
        second.join(timeout=5)

        results = [result_queue.get_nowait() for _ in range(2)]
        assert results == [True, True], "Both sequential processes should have acquired the lock successfully"

    def test_concurrent_processes_different_locks_succeed(self, tmp_path: Path) -> None:
        """Two processes each acquiring a *different* lock concurrently must both succeed."""
        lock_path_a = str(tmp_path / "lock_a.lock")
        lock_path_b = str(tmp_path / "lock_b.lock")

        held_event = multiprocessing.Event()
        release_event = multiprocessing.Event()
        result_queue: multiprocessing.Queue = multiprocessing.Queue()  # type: ignore[type-arg]

        proc_a = multiprocessing.Process(target=self._acquire_and_hold, args=(lock_path_a, held_event, release_event))
        proc_b = multiprocessing.Process(target=self._try_acquire, args=(lock_path_b, result_queue))

        proc_a.start()
        proc_b.start()
        proc_a.join(timeout=0.1)
        proc_b.join(timeout=0.1)

        assert not result_queue.empty(), "Contender process did not report a result"
        acquired = result_queue.get_nowait()
        assert acquired is True, "Second process should NOT have acquired the already-held lock"

    @staticmethod
    def _acquire_and_hold(
        lock_path: str, held_event: "multiprocessing.Event", release_event: "multiprocessing.Event"
    ) -> None:  # type: ignore[type-arg]
        """Acquire the lock, signal that it is held, then wait for a release signal."""
        lock = AntarestFileLock(lock_path, timeout=0, blocking=False)
        lock.acquire()
        held_event.set()
        release_event.wait(timeout=5)
        lock.release()

    @staticmethod
    def _try_acquire(lock_path: str, result_queue: "multiprocessing.Queue") -> None:  # type: ignore[type-arg]
        """Try to acquire the lock and push True/False into the queue."""
        lock = AntarestFileLock(lock_path, timeout=0, blocking=False)
        try:
            lock.acquire()
            result_queue.put(True)
            lock.release()
        except LockNotAcquired:
            result_queue.put(False)
