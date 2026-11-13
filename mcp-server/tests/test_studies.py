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

from pathlib import Path
from typing import Any

import pytest

from antares_web_mcp.client import AntaresWebClient
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, call, data, error_text

pytestmark = pytest.mark.anyio

NEW_ID = "0dc18c59-71ae-455d-adfc-12db79b79f34"


def study(study_id: str, name: str, **extra: Any) -> dict[str, Any]:
    return {
        "id": study_id,
        "name": name,
        "version": "9.2",
        "type": "rawstudy",
        "owner": {"id": 1, "name": "admin"},
        "workspace": "default",
        "managed": True,
        "archived": False,
        "updated": "2026-11-07 10:00:00",
        **extra,
    }


async def test_create_study(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("POST", "/v1/studies", json_body=NEW_ID)
    fake_api.route("GET", f"/v1/studies/{NEW_ID}", json_body=study(NEW_ID, "Demo"))

    result = await call(api_client, "create_study", {"name": "Demo", "version": "8.8"})

    assert data(result)["id"] == NEW_ID
    params = fake_api.requests_to("POST", "/v1/studies")[0].url.params
    assert (params["name"], params["version"]) == ("Demo", "8.8")
    assert "directory" not in params


async def test_describe_study_lists_links_in_both_directions(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    """Antares Web stores a link only in its first area (alphabetical order)."""
    fake_api.route(
        "GET",
        f"/v1/studies/{STUDY_ID}/synthesis",
        json_body={
            "study_id": STUDY_ID,
            "version": "9.2",
            "enr_modelling": "clusters",
            "areas": {
                "be": {"name": "BE", "links": {"fr": {}}, "thermals": [], "renewables": [], "st_storages": []},
                "de": {"name": "DE", "links": {"fr": {}}, "thermals": [{"id": "gas"}], "renewables": [{"id": "wind"}]},
                "fr": {"name": "FR", "links": {}, "thermals": [{"id": "nuclear"}], "st_storages": [{"id": "battery"}]},
            },
            "outputs": {"20261107-1121eco": {}},
        },
    )

    description = data(await call(api_client, "describe_study", {"study_id": STUDY_ID}))

    areas = {area["id"]: area for area in description["areas"]}
    assert areas["fr"]["linked_to"] == ["be", "de"]
    assert areas["be"]["linked_to"] == ["fr"]
    assert areas["de"]["thermal_clusters"] == ["gas"]
    assert areas["fr"]["storages"] == ["battery"]
    assert description["outputs"] == ["20261107-1121eco"]


async def test_copy_study_waits_for_the_task(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("POST", f"/v1/studies/{STUDY_ID}/copy", json_body="task-1")
    fake_api.route(
        "GET", "/v1/tasks/task-1", json_body={"status": 3, "result": {"success": True, "returnValue": NEW_ID}}
    )
    fake_api.route("GET", f"/v1/studies/{NEW_ID}", json_body=study(NEW_ID, "Copy"))

    result = await call(api_client, "copy_study", {"study_id": STUDY_ID, "new_name": "Copy"})

    assert data(result)["name"] == "Copy"
    assert fake_api.requests_to("GET", "/v1/tasks/task-1")[0].url.params["wait_for_completion"] == "true"


async def test_copy_study_failure_is_reported(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("POST", f"/v1/studies/{STUDY_ID}/copy", json_body="task-1")
    fake_api.route(
        "GET", "/v1/tasks/task-1", json_body={"status": 4, "result": {"success": False, "message": "Disk full"}}
    )

    result = await call(api_client, "copy_study", {"study_id": STUDY_ID, "new_name": "Copy"})

    assert "Disk full" in error_text(result)


async def test_update_simulation_settings(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    path = f"/v1/studies/{STUDY_ID}/config/general/form"
    fake_api.route("PUT", path, json_body=None)
    fake_api.route("GET", path, json_body={"mode": "Adequacy", "nbYears": 1})

    result = await call(
        api_client, "update_simulation_settings", {"study_id": STUDY_ID, "nb_years": 1, "mode": "Adequacy"}
    )

    assert data(result) == {"mode": "Adequacy", "nbYears": 1}
    assert fake_api.json_sent_to("PUT", path) == [{"mode": "Adequacy", "nbYears": 1}]


async def test_update_simulation_settings_without_changes(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    result = await call(api_client, "update_simulation_settings", {"study_id": STUDY_ID})

    assert "Nothing to update" in error_text(result)
    assert fake_api.requests == []


async def test_delete_study(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("GET", f"/v1/studies/{STUDY_ID}", json_body=study(STUDY_ID, "Old"))
    fake_api.route("DELETE", f"/v1/studies/{STUDY_ID}", json_body=None)

    result = await call(
        api_client, "delete_study", {"study_id": STUDY_ID, "with_variants": True}, allow_study_deletion=True
    )

    assert "'Old'" in data(result)
    assert fake_api.requests_to("DELETE", f"/v1/studies/{STUDY_ID}")[0].url.params["children"] == "true"


async def test_import_study_uploads_the_archive(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient, tmp_path: Path
) -> None:
    archive = tmp_path / "My study.zip"
    archive.write_bytes(b"PK fake zip content")
    fake_api.route("POST", "/v1/studies/_import", json_body=NEW_ID)
    fake_api.route("GET", f"/v1/studies/{NEW_ID}", json_body=study(NEW_ID, "My study"))

    result = await call(api_client, "import_study", {"path": str(archive), "groups": ["team-a", "team-b"]})

    assert data(result)["id"] == NEW_ID
    request = fake_api.requests_to("POST", "/v1/studies/_import")[0]
    assert request.url.params["groups"] == "team-a,team-b"
    body = request.read()
    assert b'name="study"; filename="My study.zip"' in body
    assert b"PK fake zip content" in body


async def test_import_study_rejects_missing_file(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient, tmp_path: Path
) -> None:
    result = await call(api_client, "import_study", {"path": str(tmp_path / "missing.zip")})

    assert "No such file" in error_text(result)
    assert not fake_api.requests


async def test_import_study_rejects_non_archive(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient, tmp_path: Path
) -> None:
    notes = tmp_path / "notes.txt"
    notes.write_text("hello")

    result = await call(api_client, "import_study", {"path": str(notes)})

    assert ".zip or .7z" in error_text(result)
    assert not fake_api.requests
