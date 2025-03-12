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

import io
import os
import zipfile
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.serde.ini_reader import IniReader
from tests.integration.assets import ASSETS_DIR


class TestStudyVersions:
    """
    This class contains tests related to the handling of different study versions
    """

    def test_nominal_case(self, client: TestClient, user_access_token: str, tmp_path: str) -> None:
        # =============================
        #  SET UP
        # =============================
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        data = """[antares]
version = 9.0
caption = test_version_90
created = 1682506382.235618
lastsave = 1682506382.23562
author = Unknown
"""
        tmp_dir = Path(tmp_path)
        zip_path = ASSETS_DIR / "STA-mini.zip"
        # Extract zip inside tmp_dir
        new_zip_path = tmp_dir / "test_version_90"
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(new_zip_path)

        # Change file content
        target_path = os.path.join(new_zip_path, "STA-mini", "study.antares")
        with open(target_path, "w") as file:
            file.write(data)

        final_path = tmp_dir / "test_version_90.zip"
        # Rezip it
        with zipfile.ZipFile(final_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(new_zip_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, new_zip_path))

        # =============================
        #  LIFECYCLE
        # =============================

        for f in [zip_path, final_path]:
            # Imports a study
            res = client.post("/v1/studies/_import", files={"study": io.BytesIO(f.read_bytes())})
            res.raise_for_status()
            study_id = res.json()

            # Gets study information
            res = client.get(f"v1/studies/{study_id}")
            res.raise_for_status()
            assert res.json()["version"] == 900 if f == final_path else 700

            # Reads `study.version` file
            res = client.get(f"v1/studies/{study_id}/raw?path=study")
            res.raise_for_status()
            version = str(res.json()["antares"]["version"])
            assert version == "9.0" if f == final_path else "700"

            # Delete the study
            res = client.delete(f"v1/studies/{study_id}")
            res.raise_for_status()

    def test_create_study_new_version_format(self, client: TestClient, user_access_token: str, tmp_path: str) -> None:
        # Checks that requesting a study in version "8.8" (not "880") works

        # =============================
        #  SET UP
        # =============================
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # =============================
        #  LIFECYCLE
        # =============================

        res = client.post("/v1/studies?name=my-study&version=8.8")
        assert res.status_code == 201
        study_id = res.json()

        res = client.get(f"/v1/studies/{study_id}/raw/original-file?path=study")
        study_antares_content = IniReader().read(io.StringIO(res.text))
        assert str(study_antares_content["antares"]["version"]) == "880"
