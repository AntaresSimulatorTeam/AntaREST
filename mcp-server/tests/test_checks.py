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

from dataclasses import replace
from typing import Any, override

import pytest

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.tools.checks import (
    MatrixReader,
    StudyData,
    check_calendar,
    check_constraint_references,
    check_disabled_objects,
    check_hydro_generation_power,
    check_isolated_areas,
    check_link_capacities,
    check_relaxable_helper_terms,
    check_renewable_series,
    check_scenarised_constraints,
    check_storage_efficiency,
    check_thermal_availability,
    check_thermal_market_bid,
    check_thermal_min_stable_power,
    check_unsupplied_energy_cost,
)
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, call, data

HOURS = 8760


def thermal(**extra: Any) -> dict[str, Any]:
    return {
        "enabled": True,
        "unitCount": 1,
        "nominalCapacity": 1000.0,
        "minStablePower": 0.0,
        "marginalCost": 10.0,
        "marketBidCost": 10.0,
        "mustRun": False,
    } | extra


def study(**changes: Any) -> StudyData:
    base = StudyData(
        name="Base case",
        version="9.2",
        general={"horizon": "2030", "firstMonth": "january", "firstJanuary": "Tuesday"},  # 1 January 2030
        playlist=None,
        areas={"fr": {"energyCostUnsupplied": 10000.0}, "de": {"energyCostUnsupplied": 10000.0}},
        links={"de / fr": {"transmissionCapacities": "enabled"}},
        thermals={"fr / nuclear": thermal()},
        renewables={},
        storages={},
        constraints=[],
    )
    return replace(base, **changes)


class FakeReader(MatrixReader):
    """Serves matrices from memory: a missing path is an empty matrix (default zeros)."""

    def __init__(self, matrices: dict[str, list[list[float]]]) -> None:
        self.matrices = matrices
        self.failures = 0

    @override
    async def read(self, path: str) -> list[list[float]] | None:
        return self.matrices.get(path, [])

    @override
    async def read_all(self, paths: list[str]) -> list[list[list[float]] | None]:
        return [await self.read(path) for path in paths]


def constant(value: float, rows: int = HOURS, columns: int = 1) -> list[list[float]]:
    return [[value] * columns for _ in range(rows)]


# ----------------------------------------------------------------------
# Quick rules
# ----------------------------------------------------------------------


def test_consistent_study_has_no_finding() -> None:
    data_ = study()
    for check in (
        check_calendar,
        check_thermal_min_stable_power,
        check_thermal_market_bid,
        check_unsupplied_energy_cost,
        check_storage_efficiency,
        check_disabled_objects,
        check_isolated_areas,
        check_constraint_references,
        check_relaxable_helper_terms,
    ):
        assert check(data_) == [], check.__name__


def test_calendar_of_another_year_than_the_study_name() -> None:
    """A '2060' study simulating July 2028 - June 2029, with the 2029 calendar (1 January = Monday)."""
    general = {"horizon": "2028-2029", "firstMonth": "july", "firstJanuary": "Monday"}

    (finding,) = check_calendar(study(name="scenario_central_2060final", general=general))

    assert finding.severity == "warning"
    assert "refers to 2060 (1 January 2060 is a Thursday)" in finding.message
    assert "the 2029 calendar" in finding.message


def test_calendar_inconsistent_with_horizon() -> None:
    (finding,) = check_calendar(study(general={"horizon": "2030", "firstMonth": "january", "firstJanuary": "Monday"}))

    assert "does not match the horizon '2030'" in finding.message


def test_thermal_rules() -> None:
    data_ = study(
        thermals={
            "fr / unstable": thermal(minStablePower=1200.0),
            "fr / subsidised": thermal(marginalCost=80.0, marketBidCost=0.0),
            "fr / disabled": thermal(enabled=False, minStablePower=5000.0),
        }
    )

    assert check_thermal_min_stable_power(data_)[0].objects == ["fr / unstable (1200.0 > 1000.0 MW)"]
    assert check_thermal_market_bid(data_)[0].objects == ["fr / subsidised (bid 0.0 < cost 80.0 EUR/MWh)"]


def test_unsupplied_energy_cost() -> None:
    data_ = study(
        areas={"fr": {"energyCostUnsupplied": 50.0}, "sink": {"energyCostUnsupplied": 0.0}},
        thermals={"fr / peaker": thermal(marginalCost=300.0)},
    )

    too_low, free = check_unsupplied_energy_cost(data_)

    assert (too_low.severity, too_low.objects) == ("warning", ["fr (50 < 300 EUR/MWh)"])
    assert (free.severity, free.objects) == ("info", ["sink"])


def test_storage_efficiency_above_one() -> None:
    data_ = study(storages={"fr / v2g": {"enabled": True, "efficiency": 0.95, "efficiencyWithdrawal": 1.05}})

    assert check_storage_efficiency(data_)[0].objects == ["fr / v2g (injection 0.95, withdrawal 1.05)"]


def test_constraint_references() -> None:
    data_ = study(
        thermals={"fr / nuclear": thermal(), "se / dsr": thermal(enabled=False)},
        constraints=[
            {
                "id": "bc",
                "operator": "less",
                "terms": [
                    {"weight": 1, "data": {"area": "se", "cluster": "dsr"}},
                    {"weight": 1, "data": {"area": "fr", "cluster": "ghost"}},
                    {"weight": 1, "data": {"area1": "be", "area2": "fr"}},
                ],
            }
        ],
    )

    missing, disabled = check_constraint_references(data_)

    assert missing.objects == ["bc: fr.ghost", "bc: be / fr"]
    assert disabled.objects == ["bc: se.dsr"]


def test_relaxable_helper_terms() -> None:
    """
    `fr_production >= 0.8 x helper` never binds: the free helper production can be lowered at no cost.
    `fr_production <= 0.98 x helper` does work: it is an upper bound on the production.
    """

    def constraint(constraint_id: str, operator: str, weight: float) -> dict[str, Any]:
        terms = [
            {"weight": 1.0, "data": {"area": "fr", "cluster": "nuclear"}},
            {"weight": weight, "data": {"area": "helper", "cluster": "copy"}},
        ]
        return {"id": constraint_id, "operator": operator, "terms": terms}

    data_ = study(
        areas={"fr": {"energyCostUnsupplied": 10000.0}, "de": {}, "helper": {"energyCostUnsupplied": 0.0}},
        thermals={"fr / nuclear": thermal(), "helper / copy": thermal(marginalCost=0.0, marketBidCost=0.0)},
        constraints=[constraint("max_modulation", "greater", -0.8), constraint("max_energy", "less", -0.98)],
    )

    (finding,) = check_relaxable_helper_terms(data_)

    assert finding.objects == ["max_modulation (greater, -0.8 x helper.copy)"]
    assert check_isolated_areas(data_)[0].objects == ["helper"]


# ----------------------------------------------------------------------
# Deep rules
# ----------------------------------------------------------------------


@pytest.mark.anyio
async def test_hydro_inflows_without_generating_power() -> None:
    reader = FakeReader(
        {
            "input/hydro/series/fr/mod": constant(1000.0, rows=365),
            "input/hydro/common/capacity/maxpower_fr": constant(4666.0, columns=4, rows=365),
            "input/hydro/series/de/mod": constant(500.0, rows=365),
            "input/hydro/series/de/maxHourlyGenPower": constant(2000.0),
        }
    )

    (finding,) = await check_hydro_generation_power(study(), reader)

    assert (finding.severity, finding.objects) == ("error", ["fr"])
    assert "still declare 4,666 MW" in finding.message


@pytest.mark.anyio
async def test_thermal_availability() -> None:
    data_ = study(
        thermals={
            "fr / null": thermal(),
            "fr / rounded": thermal(unitCount=15, nominalCapacity=46.1),  # 691.5 MW, series rounded to 692
            "fr / changed": thermal(unitCount=2),
        }
    )
    reader = FakeReader(
        {
            "input/thermal/series/fr/rounded/series": constant(692.0),
            "input/thermal/series/fr/changed/series": constant(3000.0),
        }
    )

    null, above = await check_thermal_availability(data_, reader)

    assert null.objects == ["fr / null"]
    assert above.objects == ["fr / changed (3,000.0 > 2,000.0 MW)"]


@pytest.mark.anyio
async def test_renewable_series_out_of_range() -> None:
    cluster = {"enabled": True, "unitCount": 1, "nominalCapacity": 100.0, "tsInterpretation": "production-factor"}
    reader = FakeReader({"input/renewables/series/fr/wind/series": constant(80.0)})

    (finding,) = await check_renewable_series(study(renewables={"fr / wind": cluster}), reader)

    assert finding.objects == ["fr / wind (factor from 80 to 80)"]


@pytest.mark.anyio
async def test_link_capacities_and_scenarised_constraints() -> None:
    data_ = study(
        links={"de / fr": {"transmissionCapacities": "enabled"}, "be / fr": {"transmissionCapacities": "infinite"}},
        constraints=[{"id": "nuc_limit", "operator": "less", "group": "scenarised", "terms": []}],
        scenario_builder={"bc": {"scenarised": {"0": 1, "1": 2}}},
    )
    reader = FakeReader({"input/bindingconstraints/nuc_limit_lt": constant(0.0, columns=200)})

    (dead,) = await check_link_capacities(data_, reader)
    (useless,) = await check_scenarised_constraints(data_, reader)

    assert dead.objects == ["de / fr"]  # infinite capacities are not checked
    assert useless.objects == ["nuc_limit"]


# ----------------------------------------------------------------------
# Tool
# ----------------------------------------------------------------------


@pytest.mark.anyio
async def test_check_study_tool(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    base = f"/v1/studies/{STUDY_ID}"
    fake_api.route("GET", base, json_body={"id": STUDY_ID, "name": "Base case", "version": "9.2"})
    fake_api.route(
        "GET", f"{base}/config/general/form", json_body={"horizon": "2030", "firstJanuary": "Tuesday", "nbYears": 1}
    )
    fake_api.route("GET", f"{base}/table-mode/areas", json_body={"fr": {"energyCostUnsupplied": 0.0}})
    fake_api.route("GET", f"{base}/table-mode/links", json_body={})
    fake_api.route("GET", f"{base}/table-mode/thermals", json_body={"fr / nuclear": thermal(minStablePower=2000.0)})
    fake_api.route("GET", f"{base}/table-mode/renewables", json_body={})
    fake_api.route("GET", f"{base}/table-mode/st-storages", json_body={})
    fake_api.route("GET", f"{base}/bindingconstraints", json_body=[])

    report = data(await call(api_client, "check_study", {"study_id": STUDY_ID}))

    assert report["summary"] == {"error": 1, "warning": 0, "info": 1}
    assert [finding["rule"] for finding in report["findings"]] == [
        "thermal_min_stable_power",
        "unsupplied_energy_cost",
    ]
    assert "hydro_generation_power" in report["rules_skipped"]
