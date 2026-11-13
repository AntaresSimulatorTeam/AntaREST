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

"""
Tests of the MCP server, through a real MCP client connected in-process to the server
(no subprocess, no network): this exercises tool registration, JSON schema validation
of arguments and result serialization exactly as Claude or Copilot would see them.
"""

import pytest
from mcp import Client

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.server import create_server
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, call, error_text

pytestmark = pytest.mark.anyio

READ_TOOLS = {
    "list_studies",
    "get_study",
    "describe_study",
    "list_study_versions",
    "get_simulation_settings",
    "list_areas",
    "list_links",
    "get_area_properties",
    "list_clusters",
    "list_launchers",
    "get_job",
    "list_jobs",
    "wait_for_job",
    "get_job_logs",
    "list_outputs",
    "get_area_results",
    "get_link_results",
    "get_storage_results",
    "get_study_context",
    "get_study_configuration",
    "describe_monte_carlo_scenarios",
    "summarize_installed_capacity",
    "get_table",
    "get_matrix_stats",
    "list_binding_constraints",
    "read_study_file",
    "check_study",
}
WRITE_TOOLS = {
    "create_study",
    "import_study",
    "copy_study",
    "create_variant",
    "update_simulation_settings",
    "create_area",
    "delete_area",
    "update_area_properties",
    "create_link",
    "update_link",
    "set_link_capacity",
    "delete_link",
    "set_area_load",
    "create_thermal_cluster",
    "update_thermal_cluster",
    "create_renewable_cluster",
    "create_storage",
    "delete_cluster",
    "launch_study",
    "kill_job",
}
DESTRUCTIVE_TOOLS = {"delete_area", "delete_link", "delete_cluster", "kill_job"}

LINK = {"area1": "de", "area2": "fr", "assetType": "ac", "hurdlesCost": False}


async def test_list_tools(api_client: AntaresWebClient) -> None:
    async with Client(create_server(api_client)) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == READ_TOOLS | WRITE_TOOLS
    annotations = {name: tool.annotations for name, tool in tools.items()}
    for name in READ_TOOLS:
        assert (read_annotations := annotations[name]) is not None
        assert read_annotations.read_only_hint is True
    for name in DESTRUCTIVE_TOOLS:
        assert (delete_annotations := annotations[name]) is not None
        assert delete_annotations.destructive_hint is True
    # Every tool must be documented: the description is what the model reads.
    assert all(tool.description for tool in tools.values())


async def test_study_deletion_is_opt_in(api_client: AntaresWebClient) -> None:
    async with Client(create_server(api_client, allow_study_deletion=True)) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
    assert set(tools) == READ_TOOLS | WRITE_TOOLS | {"delete_study"}
    assert (annotations := tools["delete_study"].annotations) is not None
    assert annotations.destructive_hint is True

    async with Client(create_server(api_client, read_only=True, allow_study_deletion=True)) as client:
        assert "delete_study" not in {tool.name for tool in (await client.list_tools()).tools}


async def test_read_only_mode_hides_write_tools(api_client: AntaresWebClient) -> None:
    async with Client(create_server(api_client, read_only=True)) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}

    assert names == READ_TOOLS


async def test_mistyped_study_id_is_rejected_before_any_request(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    # Real case: the model copied a UUID with one extra character in its 4th group.
    mistyped = "6c556897-8451-4b7b-a64e8-a8b185144b2d"

    result = await call(api_client, "list_areas", {"study_id": mistyped})

    assert "study_id" in error_text(result)
    assert fake_api.requests == []


async def test_list_studies_returns_summaries(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route(
        "GET",
        "/v1/studies",
        json_body={
            STUDY_ID: {
                "id": STUDY_ID,
                "name": "Base case",
                "version": "9.2",
                "type": "rawstudy",
                "owner": {"id": 1, "name": "admin"},
                "groups": [{"id": "g1", "name": "group"}],
                "workspace": "default",
                "managed": True,
                "archived": False,
                "tags": ["demo"],
                "updated": "2026-10-26 10:29:51",
                "parent_id": None,
            }
        },
    )

    result = await call(api_client, "list_studies", {"name": "base"})

    assert not result.is_error
    assert result.structured_content == {
        "result": [
            {
                "id": STUDY_ID,
                "name": "Base case",
                "version": "9.2",
                "type": "rawstudy",
                "owner": "admin",
                "workspace": "default",
                "managed": True,
                "archived": False,
                "parent_id": None,
                "tags": ["demo"],
                "updated": "2026-10-26 10:29:51",
            }
        ]
    }


async def test_list_areas(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route(
        "GET",
        f"/v1/studies/{STUDY_ID}/areas",
        json_body=[{"id": "fr", "name": "FR", "thermals": [{"id": "nuclear"}], "type": "AREA"}],
    )

    result = await call(api_client, "list_areas", {"study_id": STUDY_ID})

    assert result.structured_content == {"result": [{"id": "fr", "name": "FR"}]}


async def test_create_area(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("POST", f"/v1/studies/{STUDY_ID}/areas", json_body={"id": "ile-de-france", "name": "Île-de-France"})

    result = await call(api_client, "create_area", {"study_id": STUDY_ID, "name": "Île-de-France"})

    assert fake_api.last_json() == {"name": "Île-de-France"}
    assert result.structured_content == {"id": "ile-de-france", "name": "Île-de-France"}


async def test_create_link_sends_only_provided_properties(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    fake_api.route("POST", f"/v1/studies/{STUDY_ID}/links", json_body=LINK)

    result = await call(
        api_client,
        "create_link",
        {"study_id": STUDY_ID, "area1": "fr", "area2": "de", "asset_type": "dc", "hurdles_cost": True},
    )

    assert not result.is_error
    assert fake_api.last_json() == {"area1": "fr", "area2": "de", "assetType": "dc", "hurdlesCost": True}


async def test_create_link_rejects_unknown_asset_type(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    result = await call(
        api_client, "create_link", {"study_id": STUDY_ID, "area1": "fr", "area2": "de", "asset_type": "nuclear"}
    )

    assert result.is_error
    assert fake_api.requests == []  # rejected by the MCP schema validation, before any HTTP call


async def test_update_link_orders_areas(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("PUT", f"/v1/studies/{STUDY_ID}/links/de/fr", json_body=LINK)

    result = await call(
        api_client,
        "update_link",
        {"study_id": STUDY_ID, "area1": "fr", "area2": "de", "transmission_capacities": "infinite"},
    )

    assert not result.is_error
    assert fake_api.last_json() == {"transmissionCapacities": "infinite"}


async def test_update_link_without_changes_is_an_error(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    result = await call(api_client, "update_link", {"study_id": STUDY_ID, "area1": "fr", "area2": "de"})

    assert "Nothing to update" in error_text(result)
    assert fake_api.requests == []


async def test_delete_link_orders_areas(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("DELETE", f"/v1/studies/{STUDY_ID}/links/de/fr", json_body="de%fr")

    result = await call(api_client, "delete_link", {"study_id": STUDY_ID, "area1": "fr", "area2": "de"})

    assert not result.is_error
    assert fake_api.last_request.method == "DELETE"


async def test_api_errors_are_reported_to_the_model(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route(
        "DELETE",
        f"/v1/studies/{STUDY_ID}/areas/fr",
        status_code=403,
        json_body={
            "description": "Area 'fr' is referenced by binding constraint bc1",
            "exception": "ReferencedObjectDeletionNotAllowed",
        },
    )

    result = await call(api_client, "delete_area", {"study_id": STUDY_ID, "area_id": "fr"})

    assert "ReferencedObjectDeletionNotAllowed" in error_text(result)
    assert "referenced by binding constraint" in error_text(result)
