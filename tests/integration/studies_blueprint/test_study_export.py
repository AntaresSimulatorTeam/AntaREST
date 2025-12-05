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
from starlette.testclient import TestClient


# Doing exports with both .zip and .7z
def test_export_study_with_both_compression(client: TestClient, internal_study_id: str, user_access_token: str) -> None:
    # exporting without any parameters (thus exporting in .zip by default)
    export_res = client.get(f"/v1/studies/{internal_study_id}/export", stream=True)
    export_json_res = export_res.json()
    assert ".zip" in export_json_res["file"]["filename"]

    # exporting with the .7z compression
    export_res = client.get(f"/v1/studies/{internal_study_id}/export?compression=.7z")
    export_json_res = export_res.json()
    assert ".7z" in export_json_res["file"]["filename"]

    # exporting with an unauthorized compression
    failed_export_res = client.get(f"/v1/studies/{internal_study_id}/export?compression=.rar")
    assert failed_export_res.status_code == 422, failed_export_res
