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

from typing import Any

import pytest

from antares_web_mcp.client import AntaresWebClient
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, call, data

pytestmark = pytest.mark.anyio

AREA = f"/v1/studies/{STUDY_ID}/areas/fr"
MATRIX = f"/v1/studies/{STUDY_ID}/matrix"


def matrix_edits(fake_api: FakeAntaresWeb) -> list[tuple[str, str, float]]:
    """(path, operation, value) of every matrix edition sent to Antares Web."""
    edits = []
    for request, body in zip(fake_api.requests_to("PUT", MATRIX), fake_api.json_sent_to("PUT", MATRIX)):
        (instruction,) = body
        assert instruction["slices"] == [{"row_from": 0, "row_to": 8759, "column_from": 0, "column_to": 9999}]
        edits.append(
            (request.url.params["path"], instruction["operation"]["operation"], instruction["operation"]["value"])
        )
    return edits


def thermal(**extra: Any) -> dict[str, Any]:
    return {
        "id": "Nuclear FR",
        "name": "Nuclear FR",
        "group": "nuclear",
        "unitCount": 70,
        "nominalCapacity": 1000.0,
    } | extra


async def test_create_thermal_cluster_sets_availability(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    """Without this, the cluster created through the REST API has a null availability and produces nothing."""
    fake_api.route("POST", f"{AREA}/clusters/thermal", json_body=thermal(marginalCost=15.0, marketBidCost=15.0))
    fake_api.route("PUT", MATRIX, json_body=None)

    result = await call(
        api_client,
        "create_thermal_cluster",
        {
            "study_id": STUDY_ID,
            "area_id": "fr",
            "name": "Nuclear FR",
            "group": "nuclear",
            "unit_count": 70,
            "nominal_capacity": 1000,
            "marginal_cost": 15,
        },
    )

    assert data(result)["availability_mw"] == 70000
    assert fake_api.json_sent_to("POST", f"{AREA}/clusters/thermal") == [
        {
            "name": "Nuclear FR",
            "group": "nuclear",
            "unitCount": 70,
            "nominalCapacity": 1000.0,
            "marginalCost": 15.0,
            "marketBidCost": 15.0,  # defaults to the marginal cost, otherwise the plant bids at 0
        }
    ]
    # The series path uses the lower-case cluster id.
    assert matrix_edits(fake_api) == [("input/thermal/series/fr/nuclear fr/series", "=", 70000.0)]


async def test_update_thermal_cluster_resets_availability(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    fake_api.route("PATCH", f"{AREA}/clusters/thermal/nuclear%20fr", json_body=thermal(unitCount=60))
    fake_api.route("PUT", MATRIX, json_body=None)

    result = await call(
        api_client,
        "update_thermal_cluster",
        {"study_id": STUDY_ID, "area_id": "fr", "cluster_id": "nuclear fr", "unit_count": 60, "marginal_cost": 20},
    )

    assert data(result)["availability_mw"] == 60000
    assert fake_api.json_sent_to("PATCH", f"{AREA}/clusters/thermal/nuclear%20fr") == [
        {"unitCount": 60, "marginalCost": 20.0, "marketBidCost": 20.0}
    ]
    assert matrix_edits(fake_api) == [("input/thermal/series/fr/nuclear fr/series", "=", 60000.0)]


async def test_update_thermal_cluster_cost_only_keeps_availability(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    fake_api.route("PATCH", f"{AREA}/clusters/thermal/nuclear%20fr", json_body=thermal())

    await call(
        api_client,
        "update_thermal_cluster",
        {"study_id": STUDY_ID, "area_id": "fr", "cluster_id": "nuclear fr", "marginal_cost": 20, "market_bid_cost": 18},
    )

    assert fake_api.json_sent_to("PATCH", f"{AREA}/clusters/thermal/nuclear%20fr") == [
        {"marginalCost": 20.0, "marketBidCost": 18.0}
    ]
    assert matrix_edits(fake_api) == []


async def test_create_renewable_cluster_sets_production_factor(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    fake_api.route(
        "POST",
        f"{AREA}/clusters/renewable",
        json_body={
            "id": "Wind FR",
            "name": "Wind FR",
            "group": "wind onshore",
            "tsInterpretation": "production-factor",
        },
    )
    fake_api.route("PUT", MATRIX, json_body=None)

    await call(
        api_client,
        "create_renewable_cluster",
        {
            "study_id": STUDY_ID,
            "area_id": "fr",
            "name": "Wind FR",
            "group": "wind onshore",
            "nominal_capacity": 20000,
            "capacity_factor": 0.25,
        },
    )

    assert fake_api.json_sent_to("POST", f"{AREA}/clusters/renewable")[0]["tsInterpretation"] == "production-factor"
    assert matrix_edits(fake_api) == [("input/renewables/series/fr/wind fr/series", "=", 0.25)]


@pytest.mark.parametrize("operation, symbol", [("set", "="), ("add", "+"), ("multiply", "*")])
async def test_set_area_load(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient, operation: str, symbol: str
) -> None:
    fake_api.route("PUT", MATRIX, json_body=None)

    await call(
        api_client, "set_area_load", {"study_id": STUDY_ID, "area_id": "fr", "value": 1.1, "operation": operation}
    )

    assert matrix_edits(fake_api) == [("input/load/series/load_fr", symbol, 1.1)]


async def test_create_storage(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("POST", f"{AREA}/storages", json_body={"id": "battery fr", "name": "Battery FR"})

    await call(
        api_client,
        "create_storage",
        {
            "study_id": STUDY_ID,
            "area_id": "fr",
            "name": "Battery FR",
            "injection_capacity": 1000,
            "withdrawal_capacity": 900,
            "reservoir_capacity": 4000,
        },
    )

    assert fake_api.json_sent_to("POST", f"{AREA}/storages") == [
        {
            "name": "Battery FR",
            "group": "battery",
            "injectionNominalCapacity": 1000.0,
            "withdrawalNominalCapacity": 900.0,
            "reservoirCapacity": 4000.0,
            "efficiency": 1.0,
        }
    ]


async def test_delete_cluster(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("DELETE", f"{AREA}/clusters/renewable", json_body=None)

    await call(
        api_client,
        "delete_cluster",
        {"study_id": STUDY_ID, "area_id": "fr", "kind": "renewable", "cluster_id": "wind fr"},
    )

    assert fake_api.json_sent_to("DELETE", f"{AREA}/clusters/renewable") == [["wind fr"]]
