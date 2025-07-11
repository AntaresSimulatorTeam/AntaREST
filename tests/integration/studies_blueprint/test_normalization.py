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
from pathlib import Path

from starlette.testclient import TestClient

from tests.integration.assets import ASSETS_DIR as INTEGRATION_ASSETS_DIR


class TestNormalization:
    def test_endpoint(self, client: TestClient, internal_study_id: str, user_access_token: str, tmp_path: Path) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # imports a study
        sta_mini_zip_path = INTEGRATION_ASSETS_DIR.joinpath("STA-mini.zip")
        res = client.post("/v1/studies/_import", files={"study": io.BytesIO(sta_mini_zip_path.read_bytes())})
        study_id = res.json()

        # Unzip the STA-mini study inside the tmp_path
        # Copy the files inside the managed study
        # This way we mimick the case of a raw study managed but not normalized

        ##########################
        # Nominal cases
        ##########################

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
