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

"""Tests of `survey_study`: the values out of line with comparable objects, found without any model."""

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.tools.survey import find_outliers
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, call, data
from tests.test_checks import route_study, study, thermal

AREAS = ["be", "de", "es", "fr", "it"]


def fleet(**changes: dict[str, object]) -> dict[str, dict[str, object]]:
    """One gas plant per area, identical unless changed."""
    return {f"{area} / gas": thermal(group="gas", marginalCost=70.0) | changes.get(area, {}) for area in AREAS}


def areas(**costs: float) -> dict[str, dict[str, float]]:
    return {area: {"energyCostUnsupplied": costs.get(area, 3000.0)} for area in AREAS}


def test_homogeneous_study_has_no_outlier() -> None:
    survey = find_outliers(study(areas=areas(), thermals=fleet()), peak_loads={area: 800.0 for area in AREAS})

    assert survey.observations == []
    assert survey.compared == {"thermal clusters": 5, "areas": 5, "areas with a load": 5}


def test_cost_out_of_line_with_the_group() -> None:
    """70 EUR/MWh typed as 7000: 100 times the other gas plants."""
    survey = find_outliers(study(areas=areas(), thermals=fleet(es={"marginalCost": 7000.0})), peak_loads={})

    (observation,) = survey.observations
    assert (observation.kind, observation.object) == ("thermal_marginal_cost", "es / gas")
    assert (observation.value, observation.reference) == (7000.0, 70.0)
    assert "100 times the median of the 5 clusters of group 'gas'" in observation.message


def test_small_groups_are_not_compared() -> None:
    """With two plants, none is the odd one."""
    two = {"fr / gas": thermal(group="gas", marginalCost=70.0), "de / gas": thermal(group="gas", marginalCost=7000.0)}

    assert find_outliers(study(thermals=two), peak_loads={}).observations == []


def test_unit_capacity_out_of_line_with_the_group() -> None:
    """A capacity in kW instead of MW."""
    survey = find_outliers(study(areas=areas(), thermals=fleet(it={"nominalCapacity": 1_000_000.0})), peak_loads={})

    (observation,) = survey.observations
    assert (observation.kind, observation.object) == ("thermal_unit_capacity", "it / gas")


def test_unsupplied_energy_cost_differs_from_the_other_areas() -> None:
    survey = find_outliers(study(areas=areas(de=300.0), thermals=fleet()), peak_loads={})

    (observation,) = survey.observations
    assert (observation.kind, observation.object) == ("unsupplied_energy_cost", "de")
    assert "4 of 5 areas use 3000 EUR/MWh" in observation.message


def test_capacity_far_above_the_peak_load() -> None:
    peak_loads = {area: 800.0 for area in AREAS} | {"fr": 5.0}

    survey = find_outliers(study(areas=areas(), thermals=fleet()), peak_loads=peak_loads)

    (observation,) = survey.observations
    assert (observation.kind, observation.object) == ("capacity_to_peak_load", "fr")
    assert "200 times its peak load" in observation.message


async def test_survey_study_tool(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    base = route_study(fake_api)
    del fake_api.routes[("GET", f"{base}/table-mode/areas")], fake_api.routes[("GET", f"{base}/table-mode/thermals")]
    fake_api.route("GET", f"{base}/table-mode/areas", json_body=areas())
    fake_api.route("GET", f"{base}/table-mode/thermals", json_body=fleet(es={"marginalCost": 7000.0}))

    survey = data(await call(api_client, "survey_study", {"study_id": STUDY_ID}))

    assert [observation["object"] for observation in survey["observations"]] == ["es / gas"]
    assert survey["notes"]  # the load series of the fake server cannot be read: said, not hidden
