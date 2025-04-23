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
The aim of this module is to contain fixtures for
instantiating objects such as users, studies, ...
"""

import pytest

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import User


def create_admin_user() -> User:
    with db(commit_on_exit=True):
        user = User(id=DEFAULT_ADMIN_USER.id)
        db.session.add(user)
    return DEFAULT_ADMIN_USER


@pytest.fixture
def admin_user() -> User:
    return create_admin_user()
