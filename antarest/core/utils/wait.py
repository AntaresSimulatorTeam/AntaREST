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
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def wait_for(fn: Callable[[], T | None], polling_interval: float, timeout: float) -> T | None:
    """
    Polls at regular intervals the provided function for a non-None result, until timeout (seconds) is expired.

    Note that this method will not raise on timeout, you may check for None result instead.

    Args:
        fn: polling function
        polling_interval: wait time between 2 calls of fn
        timeout: maximum time to wait.

    Returns:
        None if timed out, else the result of the function.
    """
    end = time.time() + timeout

    while time.time() < end:
        result = fn()
        if result is not None:
            return result
        time.sleep(polling_interval)

    # one last try
    return fn()
