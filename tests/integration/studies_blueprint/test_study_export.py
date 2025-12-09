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
import zipfile

import py7zr
from starlette.testclient import TestClient


# Doing exports with both .zip and .7z
def test_export_study_with_both_compression(
    client: TestClient, internal_study_id: str, admin_access_token: str, tmp_path
) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}
    base_path = tmp_path / "tmp"
    # exporting without any parameters (thus exporting in .zip by default)
    export_res = client.get(f"/v1/studies/{internal_study_id}/export")
    json_export_download_id = export_res.json()["file"]["id"]

    download_res = client.get(f"/v1/downloads/{json_export_download_id}/metadata?wait_for_availability=True").json()[
        "id"
    ]
    download_content_res = client.get(f"/v1/downloads/{download_res}")

    with open(base_path / "export.zip", "wb") as f:
        f.write(download_content_res.content)
        assert zipfile.is_zipfile(base_path / "export.zip")

    # exporting with the .7z compression
    export_res = client.get(f"/v1/studies/{internal_study_id}/export?compression=.7z")

    json_export_download_id = export_res.json()["file"]["id"]

    download_res = client.get(f"/v1/downloads/{json_export_download_id}/metadata?wait_for_availability=True").json()[
        "id"
    ]
    download_content_res = client.get(f"/v1/downloads/{download_res}")

    with open(base_path / "export.7z", "wb") as f:
        f.write(download_content_res.content)
        assert py7zr.is_7zfile(base_path / "export.7z")

    # exporting with an unauthorized compression
    failed_export_res = client.get(f"/v1/studies/{internal_study_id}/export?compression=.rar")
    assert failed_export_res.status_code == 422, failed_export_res
