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

import pytest
from starlette.testclient import TestClient

_OUTPUT_IDS = [
    "20201014-1425eco-goodbye",
    "20201014-1427eco",
    "20241807-1540eco-extra-outputs",
]


@pytest.fixture(params=["file", "v2"])
def storage_type(request, client: TestClient, user_access_token: str, internal_study_id: str) -> str:
    if request.param == "v2":
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        for output_id in _OUTPUT_IDS:
            res = client.post(
                f"/v1/studies/{internal_study_id}/output/{output_id}/_convert",
                params={"storage_type": "V2"},
            )
            assert res.status_code == 200, f"Failed to convert {output_id}: {res.text}"
    return request.param
