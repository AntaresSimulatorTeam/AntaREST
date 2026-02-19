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
from pathlib import Path

from starlette.testclient import TestClient

from tests.integration.utils import wait_for


def download_to_file(client: TestClient, download_id: str, target: Path) -> None:
    """
    Wait for download to be ready and downloads it to target file.
    """

    # Wait download
    def is_ready() -> bool:
        return client.get(f"/v1/downloads/{download_id}/metadata").json()["ready"]

    wait_for(is_ready, sleep_time=0.05)

    # Actually download
    with client.stream("GET", f"/v1/downloads/{download_id}") as res, open(target, "wb") as f:
        for chunk in res.iter_bytes():
            f.write(chunk)
    assert res.status_code == 200
