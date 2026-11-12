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

import pytest

from antares_web_mcp.client import AntaresWebClient
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, call, data, error_text

pytestmark = pytest.mark.anyio

MATRIX = f"/v1/studies/{STUDY_ID}/matrix"


@pytest.mark.parametrize(
    "area1, area2",
    [("de", "fr"), ("fr", "de")],  # the link is stored as de / fr whatever the order given by the model
)
async def test_set_link_capacity_directions(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient, area1: str, area2: str
) -> None:
    fake_api.route("PUT", MATRIX, json_body=None)
    capacities = {"de": 1000.0, "fr": 3000.0}  # capacity *from* each area

    result = await call(
        api_client,
        "set_link_capacity",
        {
            "study_id": STUDY_ID,
            "area1": area1,
            "area2": area2,
            "capacity_1_to_2": capacities[area1],
            "capacity_2_to_1": capacities[area2],
        },
    )

    assert data(result) == "Link de / fr: 1000 MW from de to fr, 3000 MW from fr to de."
    edits = {
        request.url.params["path"]: body[0]["operation"]["value"]
        for request, body in zip(fake_api.requests_to("PUT", MATRIX), fake_api.json_sent_to("PUT", MATRIX))
    }
    assert edits == {"input/links/de/capacities/fr_direct": 1000.0, "input/links/de/capacities/fr_indirect": 3000.0}


async def test_set_link_capacity_is_symmetric_by_default(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    fake_api.route("PUT", MATRIX, json_body=None)

    await call(
        api_client, "set_link_capacity", {"study_id": STUDY_ID, "area1": "fr", "area2": "be", "capacity_1_to_2": 5000}
    )

    assert [body[0]["operation"]["value"] for body in fake_api.json_sent_to("PUT", MATRIX)] == [5000.0, 5000.0]


async def test_update_area_properties(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    path = f"/v1/studies/{STUDY_ID}/areas/fr/properties/form"
    fake_api.route("PUT", path, json_body=None)
    fake_api.route("GET", path, json_body={"energyCostUnsupplied": 10000.0})

    result = await call(
        api_client, "update_area_properties", {"study_id": STUDY_ID, "area_id": "fr", "unsupplied_energy_cost": 10000}
    )

    assert data(result) == {"energyCostUnsupplied": 10000.0}
    assert fake_api.json_sent_to("PUT", path) == [{"energyCostUnsupplied": 10000.0}]


async def test_update_area_properties_without_changes(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    result = await call(api_client, "update_area_properties", {"study_id": STUDY_ID, "area_id": "fr"})

    assert "Nothing to update" in error_text(result)
