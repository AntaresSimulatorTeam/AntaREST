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
import io
from pathlib import Path

from starlette.testclient import TestClient

from tests.integration.assets import ASSETS_DIR as INTEGRATION_ASSETS_DIR


class TestCacheInvalidation:
    def test_endpoint(self, client: TestClient, user_access_token: str, tmp_path: Path) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Import a raw study, managed on disk.
        sta_mini_zip_path = INTEGRATION_ASSETS_DIR.joinpath("STA-mini.zip")
        res = client.post("/v1/studies/_import", files={"study": io.BytesIO(sta_mini_zip_path.read_bytes())})
        study_id = res.json()

        # First read warms the study config cache.
        res = client.get(f"/v1/studies/{study_id}/areas")
        assert res.status_code == 200
        initial_areas = [area["id"] for area in res.json()]
        assert len(initial_areas) > 1

        # Remove an area directly on disk, bypassing the API.
        area_list_path = tmp_path / "internal_workspace" / study_id / "input" / "areas" / "list.txt"
        kept_areas = area_list_path.read_text().splitlines()
        removed_area = kept_areas.pop()
        area_list_path.write_text("\n".join(kept_areas) + "\n")

        # The cache is now stale: the removed area is still reported.
        res = client.get(f"/v1/studies/{study_id}/areas")
        assert res.status_code == 200
        assert removed_area.lower() in [area["id"] for area in res.json()]

        # Invalidate the cache.
        res = client.put(f"/v1/studies/{study_id}/cache/_invalidate")
        assert res.status_code == 204

        # The next read rebuilds the config from disk: the area is gone.
        res = client.get(f"/v1/studies/{study_id}/areas")
        assert res.status_code == 200
        assert removed_area.lower() not in [area["id"] for area in res.json()]
