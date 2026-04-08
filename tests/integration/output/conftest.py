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

from datetime import datetime

import pytest
from starlette.testclient import TestClient

_OUTPUT_IDS = [
    "20201014-1425eco-goodbye",
    "20201014-1427eco",
    "20241807-1540eco-extra-outputs",
]


def _expected_name(timestamp: int, mode: str, name: str = "") -> str:
    date = datetime.fromtimestamp(timestamp).strftime("%Y%m%d-%H%M")
    suffix = f"-{name}" if name else ""
    return f"{date}{mode}{suffix}"


# Timestamps and metadata from the info.antares-output files in STA-mini.zip
_OUTPUT_NAME_MAP = {
    "20201014-1425eco-goodbye": _expected_name(1602678304, "eco", "goodbye"),
    "20201014-1427eco": _expected_name(1602678424, "eco"),
    "20241807-1540eco-extra-outputs": _expected_name(1718712901, "eco"),
}


@pytest.fixture(params=["file", "v2"])
def storage_type(request, client: TestClient, user_access_token: str, internal_study_id: str):
    """Parametrized fixture that runs tests with both file and parquet (V2) storage.

    Returns (mode, output_name_map) where output_name_map translates original output IDs
    to their V2 names (which may differ due to timezone-dependent name reconstruction).
    """
    if request.param == "file":
        return "file", {}

    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    for output_id in _OUTPUT_IDS:
        res = client.post(
            f"/v1/studies/{internal_study_id}/output/{output_id}/_convert",
            params={"storage_type": "V2"},
        )
        assert res.status_code == 200, f"Failed to convert {output_id}: {res.text}"

    return "v2", _OUTPUT_NAME_MAP
