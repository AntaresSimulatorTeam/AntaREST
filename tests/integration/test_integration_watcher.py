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

from fastapi import FastAPI
from starlette.testclient import TestClient


def test_integration_xpansion(app: FastAPI, tmp_path: str):
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post("/v1/login", json={"username": "admin", "password": "admin"})
    admin_credentials = res.json()
    headers = {"Authorization": f"Bearer {admin_credentials['access_token']}"}

    client.post("/v1/watcher/_scan", headers=headers)
    client.post("/v1/watcher/_scan?path=/tmp", headers=headers)
