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
import shutil
import zipfile
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.assets import ASSETS_DIR as INTEGRATION_ASSETS_DIR


class TestNormalization:
    def test_endpoint(self, client: TestClient, internal_study_id: str, user_access_token: str, tmp_path: Path) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # imports a study
        sta_mini_zip_path = INTEGRATION_ASSETS_DIR.joinpath("STA-mini.zip")
        res = client.post("/v1/studies/_import", files={"study": io.BytesIO(sta_mini_zip_path.read_bytes())})
        study_id = res.json()

        # Unzip the STA-mini study inside the tmp_path
        denormalized_path = tmp_path / "denormalized_study"
        with zipfile.ZipFile(sta_mini_zip_path, mode="r") as zipf:
            zipf.extractall(denormalized_path)
        # Copy the files inside the managed study
        # This way we mimick the case of a raw study managed but not normalized
        shutil.rmtree(denormalized_path / "STA-mini" / "output")
        internal_path = tmp_path / "internal_workspace" / study_id
        shutil.rmtree(internal_path)
        shutil.copytree(denormalized_path / "STA-mini", internal_path)

        ##########################
        # Nominal cases
        ##########################

        # Checks disk usage before
        res = client.get(f"/v1/studies/{study_id}/disk-usage")
        assert res.status_code == 200
        disk_usage = res.json()
        assert 6 * 1024 * 1024 < disk_usage < 8 * 1024 * 1024

        # Normalize the study
        res = client.put(f"/v1/studies/{study_id}/normalize")
        assert res.status_code == 200

        # Checks disk usage after. It should be way lower
        res = client.get(f"/v1/studies/{study_id}/disk-usage")
        assert res.status_code == 200
        disk_usage = res.json()
        assert disk_usage < 0.5 * 1024 * 1024

        ##########################
        # Error cases
        ##########################

        # Ensures we can't normalize an unmanaged study
        res = client.put(f"/v1/studies/{internal_study_id}/normalize")
        assert res.status_code == 422
        result = res.json()
        assert result["exception"] == "NotAManagedStudyException"
        assert result["description"] == f"Study {internal_study_id} is not managed"

        # Ensures we can't normalize a variant study
        res = client.post(f"/v1/studies/{study_id}/variants?name=variant")
        variant_id = res.json()
        res = client.put(f"/v1/studies/{variant_id}/normalize")
        assert res.status_code == 400
        result = res.json()
        assert result["exception"] == "UnsupportedOperationOnThisStudyType"
        assert (
            result["description"]
            == f"You cannot normalize the study '{variant_id}'. This is only available for raw studies."
        )

        # Archive the parent study
        res = client.put(f"/v1/studies/{study_id}/archive")
        assert res.status_code == 200
        task_id = res.json()
        res = client.get(f"/v1/tasks/{task_id}?wait_for_completion=True")
        task = res.json()
        assert task["status"] == TaskStatus.COMPLETED.value
        assert task["result"]["success"]
        # Ensures we can't normalize an archived study
        res = client.put(f"/v1/studies/{study_id}/normalize")
        assert res.status_code == 400
        result = res.json()
        assert result["exception"] == "UnsupportedOperationOnArchivedStudy"
        assert result["description"] == f"Study {study_id} is archived"
