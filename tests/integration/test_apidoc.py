
# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from starlette.testclient import TestClient

from antarest import __version__


def test_apidoc(client: TestClient) -> None:
    # Local import to avoid breaking all tests if FastAPI changes its API
    from fastapi.openapi.utils import get_openapi

    routes = client.app.routes
    openapi = get_openapi(title="Antares Web", version=__version__, routes=routes)
    assert openapi
