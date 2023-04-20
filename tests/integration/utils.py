import contextlib
import time
from typing import Callable


def wait_for(
    predicate: Callable[[], bool], timeout: float = 10, sleep_time: float = 1
) -> None:
    end = time.time() + timeout
    while time.time() < end:
        with contextlib.suppress(Exception):
            if predicate():
                return
        time.sleep(sleep_time)
    raise TimeoutError(f"task is still in progress after {timeout} seconds")
