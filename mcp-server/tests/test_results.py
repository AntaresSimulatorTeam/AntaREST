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

OUTPUT_ID = "20261107-1121eco"
AGGREGATE = f"/v1/studies/{STUDY_ID}/outputs/{OUTPUT_ID}/aggregate"

# Excerpt of a real aggregated output (the real file has ~155 columns).
AREAS_CSV = """\
area,timeId,OV. COST EXP,OV. COST STD,MRG. PRICE EXP,MRG. PRICE STD,LOAD EXP,UNSP. ENRG EXP,LOLD EXP,LOLP VALUES,NUCLEAR EXP,GAS EXP,COAL EXP
be,1,5197920000.0,0.0,84.9995,0.0,104832000.0,0.0,0.0,0.0,,61152000.0,0.0
fr,1,9172800000.0,0.0,55.3273,1.5,524160000.0,0.0,0.0,0.0,611520000.0,,0.0
"""
LINKS_CSV = """\
link,timeId,FLOW LIN. EXP,UCAP LIN. EXP,CONG. PROB + VALUES,CONG. PROB - VALUES
be - fr,1,-43680000.0,43680000.0,0.0,100.0
de - fr,1,-43680000.0,43680000.0,0.0,100.0
"""
# Real header of the short-term storage details file: no statistic suffix, one row per storage.
STORAGES_CSV = """\
area,cluster,timeId,CashFlow - Euro,Levels - MWh,P-injection - MW,P-withdrawal - MW
fr,STEP France,1,0.0,50000.0,0.0,0.0
fr,STEP France,2,1200.0,49000.0,0.0,1000.0
nl,Batterie Pays-Bas,1,0.0,4000.0,0.0,0.0
"""


def route_aggregate(fake_api: FakeAntaresWeb, target: str, csv: str) -> None:
    fake_api.route("GET", f"{AGGREGATE}/{target}/mc-all", json_body="download-1")
    fake_api.route("GET", "/v1/downloads/download-1/metadata", json_body={"ready": True, "failed": False})
    fake_api.route("GET", "/v1/downloads/download-1", text=csv)


async def test_area_results_default_indicators(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    route_aggregate(fake_api, "areas", AREAS_CSV)

    table = data(await call(api_client, "get_area_results", {"study_id": STUDY_ID, "output_id": OUTPUT_ID}))

    # Key indicators first, then the production groups that are not empty (COAL is all zeros).
    assert table["columns"] == [
        "area",
        "time",
        "OV. COST",
        "MRG. PRICE",
        "LOAD",
        "UNSP. ENRG",
        "LOLD",
        "GAS",
        "NUCLEAR",
    ]
    assert table["rows"][1] == {
        "area": "fr",
        "time": 1,
        "OV. COST": 9172800000.0,
        "MRG. PRICE": 55.3273,
        "LOAD": 524160000.0,
        "UNSP. ENRG": 0.0,
        "LOLD": 0.0,
        "GAS": None,
        "NUCLEAR": 611520000.0,
    }
    params = fake_api.requests_to("GET", f"{AGGREGATE}/areas/mc-all")[0].url.params
    assert (params["query_file"], params["frequency"], params["format"]) == ("values", "annual", "csv")
    assert (
        fake_api.requests_to("GET", "/v1/downloads/download-1/metadata")[0].url.params["wait_for_availability"]
        == "true"
    )


async def test_area_results_selection(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    route_aggregate(fake_api, "areas", AREAS_CSV)

    table = data(
        await call(
            api_client,
            "get_area_results",
            {
                "study_id": STUDY_ID,
                "output_id": OUTPUT_ID,
                "areas": ["FR"],
                "indicators": ["mrg price", "lolp"],  # case and punctuation insensitive, prefix allowed
                "statistic": "STD",
            },
        )
    )

    assert table["columns"] == ["area", "time", "MRG. PRICE", "LOLP"]
    assert table["rows"] == [{"area": "fr", "time": 1, "MRG. PRICE": 1.5, "LOLP": 0.0}]
    assert fake_api.requests_to("GET", f"{AGGREGATE}/areas/mc-all")[0].url.params["areas_ids"] == "FR"


async def test_area_results_unknown_indicator(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    route_aggregate(fake_api, "areas", AREAS_CSV)

    result = await call(
        api_client, "get_area_results", {"study_id": STUDY_ID, "output_id": OUTPUT_ID, "indicators": ["PRICE"]}
    )

    assert "Unknown indicator 'PRICE'. Available indicators: ['COAL', 'GAS', 'LOAD'" in error_text(result)


async def test_area_results_ignores_unknown_indicators(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    route_aggregate(fake_api, "areas", AREAS_CSV)

    table = data(
        await call(
            api_client,
            "get_area_results",
            {"study_id": STUDY_ID, "output_id": OUTPUT_ID, "areas": ["fr"], "indicators": ["MRG. PRICE", "H. GEN"]},
        )
    )

    # The known indicator is returned, the guessed one is reported instead of failing the whole call.
    assert table["columns"] == ["area", "time", "MRG. PRICE"]
    assert table["rows"] == [{"area": "fr", "time": 1, "MRG. PRICE": 55.3273}]
    assert table["ignored_indicators"] == ["H. GEN"]
    assert "MRG. PRICE" in table["available_indicators"]


async def test_area_results_truncation(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    route_aggregate(fake_api, "areas", AREAS_CSV)

    table = data(
        await call(api_client, "get_area_results", {"study_id": STUDY_ID, "output_id": OUTPUT_ID, "max_rows": 1})
    )

    assert (len(table["rows"]), table["total_rows"], table["truncated"]) == (1, 2, True)


async def test_link_results(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    route_aggregate(fake_api, "links", LINKS_CSV)

    table = data(
        await call(api_client, "get_link_results", {"study_id": STUDY_ID, "output_id": OUTPUT_ID, "links": ["de - fr"]})
    )

    assert table["columns"] == ["link", "time", "FLOW LIN.", "UCAP LIN.", "CONG. PROB +", "CONG. PROB -"]
    assert table["rows"] == [
        {
            "link": "de - fr",
            "time": 1,
            "FLOW LIN.": -43680000.0,
            "UCAP LIN.": 43680000.0,
            "CONG. PROB +": 0.0,
            "CONG. PROB -": 100.0,
        }
    ]


async def test_storage_results(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    route_aggregate(fake_api, "areas", STORAGES_CSV)

    table = data(
        await call(
            api_client,
            "get_storage_results",
            {"study_id": STUDY_ID, "output_id": OUTPUT_ID, "frequency": "hourly", "areas": ["FR"]},
        )
    )

    assert table["columns"] == [
        "area",
        "cluster",
        "time",
        "P-injection - MW",
        "P-withdrawal - MW",
        "Levels - MWh",
        "CashFlow - Euro",
    ]
    assert table["rows"][1] == {
        "area": "fr",
        "cluster": "STEP France",
        "time": 2,
        "P-injection - MW": 0.0,
        "P-withdrawal - MW": 1000.0,
        "Levels - MWh": 49000.0,
        "CashFlow - Euro": 1200.0,
    }
    assert table["total_rows"] == 2
    params = fake_api.requests_to("GET", f"{AGGREGATE}/areas/mc-all")[0].url.params
    assert (params["query_file"], params["frequency"], params["areas_ids"]) == ("details-STstorage", "hourly", "FR")


async def test_failed_download_is_reported(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("GET", f"{AGGREGATE}/areas/mc-all", json_body="download-1")
    fake_api.route(
        "GET", "/v1/downloads/download-1/metadata", json_body={"failed": True, "error_message": "Output not found"}
    )

    result = await call(api_client, "get_area_results", {"study_id": STUDY_ID, "output_id": OUTPUT_ID})

    assert "Output not found" in error_text(result)
