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

"""Fixtures for maintenance tests."""

from unittest import mock

import pytest

from antarest.core.config import Config


def load_config_mock() -> None:
    pass


def get_config_mock() -> Config:
    return Config()


# Explanation:
#   The Celery app setup requires to initialize it at the module level.
#   Here in tests, we override the initialization functions used in prod, otherwise they will raise because
#   they require the env var ANTARES_CONF to be filled with a path to a working configuration.
#
#   We perform that import here in conftest, so that all tests in the directory do not need to do it again.
with (
    mock.patch("antarest.maintenance.config.load_config", load_config_mock),
    mock.patch("antarest.maintenance.config.get_config", get_config_mock),
):
    import antarest.maintenance.app  # noqa


@pytest.fixture
def with_no_maintenance_ctx():
    """
    Set maintenance_ctx to None and restore after test.

    Celery's Settings object doesn't work well with standard mocking,
    so we directly manipulate and restore the global state.
    """
    mock.patch("antarest.maintenance.app._load_config", lambda x: None)

    from antarest.maintenance.app import celery_app

    original_ctx = getattr(celery_app.conf, "maintenance_ctx", None)
    celery_app.conf.maintenance_ctx = None
    yield
    celery_app.conf.maintenance_ctx = original_ctx
