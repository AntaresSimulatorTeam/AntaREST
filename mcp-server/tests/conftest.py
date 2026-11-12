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

import httpx2
import pytest

from antares_web_mcp.client import AntaresWebClient
from tests.fake_antares_web import BASE_URL, FakeAntaresWeb


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def fake_api() -> FakeAntaresWeb:
    return FakeAntaresWeb()


@pytest.fixture
def api_client(fake_api: FakeAntaresWeb) -> AntaresWebClient:
    return AntaresWebClient(BASE_URL, token="secret-token", transport=httpx2.MockTransport(fake_api.handler))
