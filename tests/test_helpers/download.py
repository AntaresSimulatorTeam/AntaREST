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
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from httpx import Response
from starlette.testclient import TestClient

from tests.integration.utils import wait_for


def wait_download_ready(client: TestClient, download_id: str) -> Response:
    # Wait download
    def is_ready() -> bool:
        res = client.get(f"/v1/downloads/{download_id}/metadata")
        return res.status_code == 200 and res.json()["ready"]

    wait_for(is_ready, sleep_time=0.05)
    return client.get(f"/v1/downloads/{download_id}/metadata")


def wait_download_error(client: TestClient, download_id: str) -> Response:
    # Wait download
    def is_complete() -> bool:
        res = client.get(f"/v1/downloads/{download_id}/metadata")
        return res.status_code != 417

    wait_for(is_complete, sleep_time=0.05)
    return client.get(f"/v1/downloads/{download_id}/metadata")


def download_to_io(client: TestClient, download_id: str, target: BinaryIO) -> None:
    # Wait download
    def is_ready() -> bool:
        res = client.get(f"/v1/downloads/{download_id}/metadata")
        return res.status_code == 200 and res.json()["ready"]

    wait_for(is_ready, sleep_time=0.05)

    # Actually download
    with client.stream("GET", f"/v1/downloads/{download_id}") as res:
        for chunk in res.iter_bytes():
            target.write(chunk)
    assert res.status_code == 200


def download_to_file(client: TestClient, download_id: str, target: Path) -> None:
    """
    Wait for download to be ready and downloads it to target file.
    """
    # Actually download
    with open(target, "wb") as f:
        download_to_io(client, download_id, f)


def download_to_str(client: TestClient, download_id: str) -> str:
    """
    Wait for download to be ready and downloads it as a string.
    """
    return download_to_bytes(client, download_id).decode("utf-8")


def download_to_bytes(client: TestClient, download_id: str) -> bytes:
    """
    Wait for download to be ready and downloads it as raw bytes.
    """
    buffer = BytesIO()
    download_to_io(client, download_id, buffer)
    return buffer.getvalue()
