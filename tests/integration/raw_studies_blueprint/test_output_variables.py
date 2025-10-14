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

from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.serde.json import from_json
from tests.integration.raw_studies_blueprint.assets import ASSETS_DIR as assets_dir

ASSETS_DIR = assets_dir / "variables_metadata"


def test_get_output_variables_metadata(
    client: TestClient, user_access_token: str, internal_study_id: str, tmp_path: Path
):
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    output_id = "20201014-1425eco-goodbye"
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_id}/variables-metadata")
    expected_content = from_json((ASSETS_DIR / "res1.json").read_bytes())
    assert expected_content == res.json()
