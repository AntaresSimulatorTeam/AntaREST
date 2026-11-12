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
from mcp import Client
from mcp.types import TextContent

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.server import create_server
from antares_web_mcp.tools.analysis import (
    comments_to_text,
    describe_sequence,
    flatten_tree,
    matrix_stats,
    summarize_scenario_builder,
    term_label,
)
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, call, data, error_text

STUDY = f"/v1/studies/{STUDY_ID}"
RAW = f"{STUDY}/raw"

WX_COMMENTS = """<?xml version="1.0" encoding="UTF-8"?>
<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">
  <paragraphlayout textcolor="#000000">
    <paragraph><text>Scenario &quot;central&quot; 2060</text></paragraph>
    <paragraph><text></text></paragraph>
    <paragraph><text>Nuclear N1</text></paragraph>
  </paragraphlayout>
</richtext>
"""


def years(*series: Any) -> dict[str, Any]:
    """Scenario builder mapping {year: series} (years are 0-based)."""
    return {str(year): value for year, value in enumerate(series)}


# ----------------------------------------------------------------------
# Pure helpers
# ----------------------------------------------------------------------


def test_comments_to_text() -> None:
    assert comments_to_text(WX_COMMENTS) == 'Scenario "central" 2060\nNuclear N1'
    assert comments_to_text('<?xml version="1.0"?><richtext><paragraph><text></text></paragraph></richtext>') == ""
    assert comments_to_text("  plain text  ") == "plain text"


def test_matrix_stats() -> None:
    stats = matrix_stats([[1, 10], [3, 30]])

    assert (stats.rows, stats.columns, stats.min, stats.max, stats.mean) == (2, 2, 1, 30, 11)
    assert stats.column_sums is not None
    assert (stats.column_sums.min, stats.column_sums.max) == (4, 40)
    assert not stats.all_zero and not stats.constant and not stats.identical_columns


def test_matrix_stats_of_empty_and_identical_matrices() -> None:
    assert matrix_stats([]).all_zero  # an empty matrix means default zeros for Antares Web
    identical = matrix_stats([[5, 5], [7, 7]])
    assert identical.identical_columns and not identical.constant


@pytest.mark.parametrize(
    "sequence, expected",
    [
        ((1, 2, 3, 1, 2, 3), "cycle over series 1 to 3 (year y uses series y mod 3 + 1)"),
        ((2, 2, 2), "always 2"),
        (("", "", ""), "random draw every year"),
        ((1, "", 1), "always 1 (1 years drawn at random)"),
        ((3, 1, 2), "custom mapping over 3 distinct values"),
    ],
)
def test_describe_sequence(sequence: tuple[Any, ...], expected: str) -> None:
    assert describe_sequence(sequence) == expected


def test_summarize_scenario_builder_detects_climatic_consistency() -> None:
    """6 years = 3 climatic years (load, hydro) x 2 availability draws (thermal): 6 distinct years."""
    rules = {
        "l": {"fr": years(1, 2, 3, 1, 2, 3), "de": years(1, 2, 3, 1, 2, 3)},
        "h": {"fr": years(1, 2, 3, 1, 2, 3)},
        "t": {"fr": {"nuclear": years(1, 2, 1, 2, 1, 2)}},
    }

    summaries, distinct, notes = summarize_scenario_builder(rules, 6)

    assert distinct == 6
    by_symbol = {summary.symbol: summary for summary in summaries}
    assert by_symbol["t"].groups[0].examples == ["fr / nuclear"]
    assert by_symbol["t"].groups[0].same_as_load is False
    assert by_symbol["h"].groups[0].same_as_load is True
    assert notes[0].startswith("All 2 load areas share the same mapping: cycle over series 1 to 3")
    assert any("rule 'h'" in note for note in notes)


def test_flatten_tree_and_term_label() -> None:
    tree = {"notes.txt": {}, "VE": {"conso.csv": {}, "old": {"a.csv": "file://a.csv"}}}
    assert flatten_tree(tree, "user") == ["user/notes.txt", "user/VE/conso.csv", "user/VE/old/a.csv"]

    assert term_label({"weight": 0.744, "data": {"area1": "fr", "area2": "z_p2g"}}) == "0.744 x flow(fr -> z_p2g)"
    assert term_label({"weight": -1.0, "offset": 2, "data": {"area": "fr", "cluster": "epr"}}) == (
        "-1 x fr.epr [offset 2h]"
    )


# ----------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_study_context_of_a_variant(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route(
        "GET",
        STUDY,
        json_body={"id": STUDY_ID, "name": "Nuclear 55 GW", "version": "9.2", "type": "variantstudy", "tags": ["N1"]},
    )
    fake_api.route("GET", f"{STUDY}/comments", json_body=WX_COMMENTS)
    fake_api.route("GET", f"{STUDY}/parents", json_body=[{"id": "base-id", "name": "Base case"}])
    fake_api.route("GET", f"{STUDY}/districts", json_body=[{"id": "fr_and_neighbours", "areas": ["fr", "be"]}])
    fake_api.route("GET", RAW, params={"path": "user"}, json_body={"notes.txt": {}, "VE": {"conso.csv": {}}})
    fake_api.route("GET", RAW, params={"path": "logs"}, json_body={"log_generation_study.txt": {}})
    fake_api.route(
        "GET",
        f"{STUDY}/commands",
        json_body=[{"action": "update_thermal_clusters", "args": {"fr": {"nuclear": {"unit_count": 55}}}}],
    )

    context = data(await call(api_client, "get_study_context", {"study_id": STUDY_ID}))

    assert context["comments"] == 'Scenario "central" 2060\nNuclear N1'
    assert context["parents"] == ["Base case (base-id)"]
    assert context["variant_changes"] == ['update_thermal_clusters: {"fr": {"nuclear": {"unit_count": 55}}}']
    assert context["output_aggregations"] == ["fr_and_neighbours: 2 areas"]
    assert context["user_files"] == ["user/notes.txt", "user/VE/conso.csv"]
    assert context["log_files"] == ["logs/log_generation_study.txt"]


@pytest.mark.anyio
async def test_get_study_configuration(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("GET", f"{STUDY}/config/general/form", json_body={"mode": "Economy", "thematicTrimming": True})
    fake_api.route("GET", f"{STUDY}/config/optimization/form", json_body={"hurdleCosts": True})
    fake_api.route("GET", f"{STUDY}/config/advancedparameters/form", json_body={"unitCommitmentMode": "fast"})
    # No route for the adequacy patch: an unavailable form is reported as null.
    fake_api.route(
        "GET",
        f"{STUDY}/config/playlist/form",
        json_body={
            "1": {"status": True, "weight": 1},
            "2": {"status": False, "weight": 1},
            "3": {"status": True, "weight": 2},
        },
    )
    fake_api.route("GET", f"{STUDY}/config/thematictrimming/form", json_body={"ovCost": True, "nh3Emis": False})

    configuration = data(await call(api_client, "get_study_configuration", {"study_id": STUDY_ID}))

    assert configuration["adequacy_patch"] is None
    assert configuration["playlist"] == {"active_years": 2, "inactive_years": [2], "weighted_years": 1}
    assert configuration["disabled_output_variables"] == ["nh3Emis"]


@pytest.mark.anyio
async def test_describe_monte_carlo_scenarios(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("GET", f"{STUDY}/config/general/form", json_body={"nbYears": 4, "buildingMode": "Custom"})
    fake_api.route(
        "GET",
        f"{STUDY}/config/scenariobuilder",
        json_body={"l": {"fr": years(1, 2, 1, 2)}, "ntc": {"de / fr": years(1, 1, 1, 1)}},
    )
    fake_api.route("GET", f"{STUDY}/config/playlist/form", json_body={str(y): {"status": True} for y in range(1, 5)})

    design = data(await call(api_client, "describe_monte_carlo_scenarios", {"study_id": STUDY_ID}))

    assert (design["nb_years"], design["active_years"], design["distinct_scenarios"]) == (4, 4, 2)
    assert [rule["symbol"] for rule in design["rules"]] == ["l", "ntc"]
    assert design["rules"][1]["groups"][0]["pattern"] == "always 1"


@pytest.mark.anyio
async def test_summarize_installed_capacity(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route(
        "GET",
        f"{STUDY}/table-mode/thermals",
        json_body={
            "fr / epr": {"group": "nuclear", "unitCount": 2, "nominalCapacity": 1650, "enabled": True},
            "fr / old": {"group": "nuclear", "unitCount": 1, "nominalCapacity": 900, "enabled": False},
            "fr / placeholder": {"group": "gas", "unitCount": 1, "nominalCapacity": 0, "enabled": True},
        },
    )
    fake_api.route(
        "GET",
        f"{STUDY}/table-mode/renewables",
        json_body={"de / wind": {"group": "wind onshore", "unitCount": 1, "nominalCapacity": 500, "enabled": True}},
    )
    fake_api.route(
        "GET",
        f"{STUDY}/table-mode/st-storages",
        json_body={
            "fr / psp": {
                "group": "psp",
                "injectionNominalCapacity": 100,
                "withdrawalNominalCapacity": 90,
                "reservoirCapacity": 800,
                "enabled": True,
            }
        },
    )

    summary = data(await call(api_client, "summarize_installed_capacity", {"study_id": STUDY_ID}))

    assert [area["area"] for area in summary["areas"]] == ["fr", "de"]
    assert summary["areas"][0]["thermal_mw"] == {"nuclear": 3300.0}
    assert summary["storage_by_group"] == {"psp": {"injection_mw": 100, "withdrawal_mw": 90, "reservoir_mwh": 800}}
    assert summary["disabled_objects"] == {"thermal": 1}
    assert summary["enabled_without_capacity"] == {"thermal": 1}


@pytest.mark.anyio
async def test_get_table_filters_rows(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route(
        "GET",
        f"{STUDY}/table-mode/thermals",
        json_body={
            "fr / epr": {"unitCount": 2, "enabled": True},
            "fr / old": {"unitCount": 1, "enabled": False},
            "de / gas": {"unitCount": 3, "enabled": True},
        },
    )

    table = data(
        await call(
            api_client,
            "get_table",
            {"study_id": STUDY_ID, "kind": "thermals", "columns": ["unitCount"], "area_id": "fr", "only_enabled": True},
        )
    )

    assert table["rows"] == [{"id": "fr / epr", "unitCount": 2, "enabled": True}]
    assert fake_api.last_request.url.params["columns"] == "unitCount,enabled"


@pytest.mark.anyio
async def test_get_matrix_stats(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("GET", RAW, params={"path": "input/load/series/load_fr"}, json_body={"data": [[1, 2], [3, 4]]})
    fake_api.route("GET", "/v1/matrix/abc123", json_body={"id": "abc123", "data": [[0], [0]]})

    async with Client(create_server(api_client)) as client:  # the HTTP client is closed with the MCP session
        by_path = data(
            await client.call_tool("get_matrix_stats", {"study_id": STUDY_ID, "path": "input/load/series/load_fr"})
        )
        by_id = data(await client.call_tool("get_matrix_stats", {"study_id": STUDY_ID, "matrix_id": "abc123"}))
        both = await client.call_tool("get_matrix_stats", {"study_id": STUDY_ID, "path": "x", "matrix_id": "y"})

    assert (by_path["columns"], by_path["max"]) == (2, 4)
    assert by_id["all_zero"] is True
    assert "either `path` or `matrix_id`" in error_text(both)


@pytest.mark.anyio
async def test_list_binding_constraints(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route(
        "GET",
        f"{STUDY}/bindingconstraints",
        json_body=[
            {
                "id": "efficiency_fr",
                "name": "efficiency_FR",
                "enabled": True,
                "timeStep": "hourly",
                "operator": "equal",
                "group": "default",
                "terms": [
                    {"weight": 1.0, "data": {"area1": "h2_fr", "area2": "p2g_fr"}},
                    {"weight": 0.744, "data": {"area1": "fr", "area2": "p2g_fr"}},
                ],
            },
            {"id": "other", "name": "other", "timeStep": "daily", "operator": "both", "terms": []},
        ],
    )

    result = data(
        await call(api_client, "list_binding_constraints", {"study_id": STUDY_ID, "name_contains": "EFFICIENCY"})
    )

    assert result["total"] == 1
    (constraint,) = result["constraints"]
    assert constraint["terms"] == ["1 x flow(h2_fr -> p2g_fr)", "0.744 x flow(fr -> p2g_fr)"]
    assert constraint["rhs_matrices"] == ["input/bindingconstraints/efficiency_fr_eq"]


@pytest.mark.anyio
async def test_read_study_file_filters_lines(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    log = "Create area : FR\nScenario NA does not exist\nCreate area : DE\nScenario NA does not exist\n"
    fake_api.route("GET", RAW, params={"path": "logs/generation.txt"}, text=log, content_type="text/plain")
    fake_api.route("GET", RAW, params={"path": "user/report.xlsx"}, text="PK...", content_type="application/zip")

    async with Client(create_server(api_client)) as client:
        excerpt = data(
            await client.call_tool(
                "read_study_file",
                {"study_id": STUDY_ID, "path": "logs/generation.txt", "pattern": "not exist", "distinct": True},
            )
        )
        binary = await client.call_tool("read_study_file", {"study_id": STUDY_ID, "path": "user/report.xlsx"})

    assert excerpt == {
        "path": "logs/generation.txt",
        "total_lines": 4,
        "matching_lines": 1,
        "lines": ["Scenario NA does not exist"],
        "truncated": False,
    }
    assert "is not a text file" in error_text(binary)


@pytest.mark.anyio
async def test_analyse_study_inputs_prompt(api_client: AntaresWebClient) -> None:
    async with Client(create_server(api_client)) as client:
        prompts = {prompt.name for prompt in (await client.list_prompts()).prompts}
        result = await client.get_prompt("analyse_study_inputs", {"study": "Base case"})

    assert prompts == {"analyse_study_inputs"}
    content = result.messages[0].content
    assert isinstance(content, TextContent)
    assert 'Antares study "Base case"' in content.text
    assert "check_study" in content.text
