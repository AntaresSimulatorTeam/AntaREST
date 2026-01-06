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

"""Fixtures for maintenance tests."""

import pytest

from antarest.maintenance.app import celery_app


@pytest.fixture
def with_no_maintenance_ctx():
    """
    Set maintenance_ctx to None and restore after test.

    Celery's Settings object doesn't work well with standard mocking,
    so we directly manipulate and restore the global state.
    """
    original_ctx = getattr(celery_app.conf, "maintenance_ctx", None)
    celery_app.conf.maintenance_ctx = None
    yield
    celery_app.conf.maintenance_ctx = original_ctx
