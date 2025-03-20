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

import pytest

from antarest.core.jwt import JWTUser
from antarest.core.logging.utils import _task_id, task_context
from antarest.login.utils import get_current_user


@pytest.mark.unit_test
def test_task_context() -> None:
    user = JWTUser(id=2, type="users", impersonator=2, groups=[])
    try:
        with task_context(task_id="my-task", user=user):
            assert get_current_user() == user
            assert _task_id.get() == "my-task"
            raise RuntimeError()
    except RuntimeError:
        pass
    assert _task_id.get() is None
    assert get_current_user() is None
