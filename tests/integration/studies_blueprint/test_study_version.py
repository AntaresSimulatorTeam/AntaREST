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

from antares.study.version.upgrade_app import UpgradeApp
from starlette.testclient import TestClient

from antarest.core.serde.ini_reader import read_ini
from antarest.study.model import STUDY_VERSION_9_2
from tests.integration.assets import ASSETS_DIR


class TestStudyVersions:
    """
    This class contains tests related to the handling of different study versions
    """

    def test_nominal_case(self, client: TestClient, user_access_token: str, tmp_path: Path) -> None:
        # =============================
        #  SET UP
        # =============================
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        zip_path = ASSETS_DIR / "STA-mini.zip"

        # Creates a study in version 9.2 from the base study in version 7.0
        new_zip_path = tmp_path / "test_version_92"
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(new_zip_path)
        app = UpgradeApp(new_zip_path / "STA-mini", version=STUDY_VERSION_9_2)
        app()
        final_path = tmp_path / "test_version_92.zip"
        with zipfile.ZipFile(final_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(new_zip_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, new_zip_path))

        # =============================
        #  LIFECYCLE
        # =============================

        for f in [zip_path, final_path]:  # zip path is the study in version 7.0 and final path the one in version 9.2
            # Imports a study
            res = client.post("/v1/studies/_import", files={"study": io.BytesIO(f.read_bytes())})
            res.raise_for_status()
            study_id = res.json()

            # Gets study information
            res = client.get(f"v1/studies/{study_id}")
            res.raise_for_status()
            assert res.json()["version"] == 920 if f == final_path else 700

            # Reads `study.version` file
            res = client.get(f"v1/studies/{study_id}/raw?path=study")
            res.raise_for_status()
            version = str(res.json()["antares"]["version"])
            assert version == "9.2" if f == final_path else "700"

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
        study_antares_content = read_ini(io.StringIO(res.text))
        assert str(study_antares_content["antares"]["version"]) == "880"
