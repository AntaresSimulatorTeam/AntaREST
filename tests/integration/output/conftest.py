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
def storage_type(request, client: TestClient, user_access_token: str, internal_study_id: str):
    if request.param == "file":
        return "file", {}

    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    assert res.status_code == 200
    names_before = {o["name"] for o in res.json()}

    for output_id in _OUTPUT_IDS:
        res = client.post(
            f"/v1/studies/{internal_study_id}/output/{output_id}/_convert",
            params={"storage_type": "V2"},
        )
        assert res.status_code == 200, f"Failed to convert {output_id}: {res.text}"

    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    assert res.status_code == 200
    names_after = {o["name"] for o in res.json()}

    new_names = names_after - names_before

    output_name_map = {}
    remaining_new = set(new_names)
    for old_id in _OUTPUT_IDS:
        if old_id in names_after:
            output_name_map[old_id] = old_id
        else:
            for new_name in remaining_new:
                if new_name not in _OUTPUT_IDS:
                    output_name_map[old_id] = new_name
                    remaining_new.discard(new_name)
                    break

    return "v2", output_name_map
