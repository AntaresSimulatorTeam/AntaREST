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
from pathlib import Path

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


@pytest.fixture(params=["in_study", "outside_study", "v2"])
def storage_type(request, client: TestClient, user_access_token: str, internal_study_id: str, tmp_path: Path):
    """Parametrized fixture that runs tests with both file and parquet (V2) storage.

    Returns (mode, output_name_map) where output_name_map translates original output IDs
    to their V2 names (which may differ due to timezone-dependent name reconstruction).
    """
    if request.param == "in_study":
        return "in_study", {}

    # `OUT_OF_FILE_STUDY_TREE` part
    internal_study_output_dir = tmp_path / "ext_workspace" / "STA-mini" / "output"
    outside_study_output_dir = tmp_path / "all_outputs" / internal_study_id

    if request.param == "outside_study":
        outside_study_output_dir.mkdir()
        for output_id in _OUTPUT_IDS:
            output_path = outside_study_output_dir / output_id
            internal_study_output_dir.joinpath(output_id).rename(output_path)
        return "outside_study", {}

    # `V2` part
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    for output_id in _OUTPUT_IDS:
        res = client.post(
            f"/v1/studies/{internal_study_id}/output/{output_id}/_convert",
            params={"storage_type": "V2"},
        )
        assert res.status_code == 200, f"Failed to convert {output_id}: {res.text}"

    return "v2", _OUTPUT_NAME_MAP
