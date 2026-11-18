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

import asyncio
from typing import Any

import httpx2
import pytest

from antares_web_mcp.client import AntaresWebClient, AntaresWebError
from tests.fake_antares_web import BASE_URL, FakeAntaresWeb

STUDY_ID = "21cdcee2-fd4a-45ca-9305-46fc89959553"


async def test_sends_bearer_token(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("GET", f"/v1/studies/{STUDY_ID}/areas", json_body=[])

    await api_client.list_areas(STUDY_ID)

    assert fake_api.last_request.headers["Authorization"] == "Bearer secret-token"


async def test_no_authorization_header_without_token(fake_api: FakeAntaresWeb) -> None:
    client = AntaresWebClient(BASE_URL, transport=httpx2.MockTransport(fake_api.handler))
    fake_api.route("GET", f"/v1/studies/{STUDY_ID}/areas", json_body=[])

    await client.list_areas(STUDY_ID)

    assert "Authorization" not in fake_api.last_request.headers


async def test_list_studies_query_params(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("GET", "/v1/studies", json_body={STUDY_ID: {"id": STUDY_ID}})

    studies = await api_client.list_studies(name="craft", versions=["8.8", "9.2"], variant=False, limit=10)

    assert studies == [{"id": STUDY_ID}]
    params = fake_api.last_request.url.params
    assert params["name"] == "craft"
    assert params["versions"] == "8.8,9.2"
    assert params["variant"] == "false"
    assert params["pageSize"] == "10"
    assert params["sortBy"] == "+name"
    assert "tags" not in params
    assert "archived" not in params


async def test_path_segments_are_encoded(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    """A malicious or wrong argument must not be able to target another endpoint."""
    with pytest.raises(AntaresWebError):
        await api_client.delete_area(STUDY_ID, "../../../users/1")

    assert fake_api.last_request.url.raw_path.decode() == f"/v1/studies/{STUDY_ID}/areas/..%2F..%2F..%2Fusers%2F1"


@pytest.mark.parametrize(
    "response, expected",
    [
        (
            {"status_code": 404, "json": {"description": "s1", "exception": "StudyNotFoundError"}},
            r"HTTP 404 \(StudyNotFoundError\): s1",
        ),
        ({"status_code": 422, "json": {"detail": "bad name"}}, "HTTP 422: bad name"),  # FastAPI validation
        ({"status_code": 502, "text": "Bad Gateway"}, "HTTP 502: Bad Gateway"),
    ],
)
async def test_http_errors_are_formatted(response: dict[str, Any], expected: str) -> None:
    client = AntaresWebClient(BASE_URL, transport=httpx2.MockTransport(lambda _: httpx2.Response(**response)))

    with pytest.raises(AntaresWebError, match=expected):
        await client.get_study(STUDY_ID)


async def test_unreachable_server() -> None:
    def refuse(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("Connection refused", request=request)

    client = AntaresWebClient(BASE_URL, transport=httpx2.MockTransport(refuse))

    with pytest.raises(AntaresWebError, match=f"Cannot reach Antares Web at {BASE_URL}"):
        await client.get_study(STUDY_ID)


async def test_writes_are_sent_one_at_a_time() -> None:
    in_flight = {"GET": 0, "POST": 0}
    peak = {"GET": 0, "POST": 0}

    async def slow_server(request: httpx2.Request) -> httpx2.Response:
        in_flight[request.method] += 1
        peak[request.method] = max(peak[request.method], in_flight[request.method])
        await asyncio.sleep(0.01)
        in_flight[request.method] -= 1
        return httpx2.Response(200, json=[] if request.method == "GET" else {})

    client = AntaresWebClient(BASE_URL, transport=httpx2.MockTransport(slow_server))
    await asyncio.gather(
        *(client.create_area(STUDY_ID, f"Area {i}") for i in range(5)),
        *(client.list_areas(STUDY_ID) for _ in range(5)),
    )

    # Concurrent writes on a study can fail in Antares Web: they are serialized, reads are not.
    assert peak == {"GET": 5, "POST": 1}
