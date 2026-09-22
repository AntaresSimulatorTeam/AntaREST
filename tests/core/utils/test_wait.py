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

from antarest.core.utils.wait import wait_for


def test_wait_1st_call():
    call_count = 0

    def return_1():
        nonlocal call_count
        call_count += 1
        return 1

    res = wait_for(return_1, polling_interval=0.1, timeout=10)
    assert res == 1
    assert call_count == 1


def test_wait_returns_none_after_timeout():
    call_count = 0

    def return_none():
        nonlocal call_count
        call_count += 1
        return None

    res = wait_for(return_none, polling_interval=0.01, timeout=0.1)
    assert res is None
    assert call_count > 0


def test_wait_returns_when_fn_returns_not_none():
    call_count = 0

    def return_1_after_10_times():
        nonlocal call_count
        call_count += 1
        if call_count < 10:
            return None
        return 1

    call_count = 0
    res = wait_for(return_1_after_10_times, polling_interval=0.01, timeout=1)
    assert res == 1
    assert call_count == 10


def test_wait_raises():

    def raising_function():
        raise ValueError("Failed")

    with pytest.raises(ValueError):
        wait_for(raising_function, polling_interval=0.01, timeout=1)
