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
from string import Formatter
from typing import Any, override

import pytest

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.tools.check_messages import MESSAGES
from antares_web_mcp.tools.checks import (
    DEEP_CHECKS,
    DEEP_RULES,
    QUICK_CHECKS,
    QUICK_RULES,
    Finding,
    MatrixReader,
    StudyData,
    check_calendar,
    check_constraint_references,
    check_disabled_objects,
    check_hydro_generation_power,
    check_isolated_areas,
    check_link_capacities,
    check_playlist,
    check_relaxable_helper_terms,
    check_renewable_series,
    check_scenarised_constraints,
    check_storage_efficiency,
    check_thermal_availability,
    check_thermal_market_bid,
    check_thermal_min_stable_power,
    check_unsupplied_energy_cost,
    load_study_data,
)
from antares_web_mcp.tools.common import Language
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

    # The expected day is in the message: a model explaining the finding must not have to compute it.
    assert "1 January is set to a Monday, but 1 January 2030 is a Tuesday" in finding.message


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


def hydro_reader() -> FakeReader:
    """`fr` declares its generating power in the legacy file only, `de` in the hourly series only."""
    return FakeReader(
        {
            "input/hydro/series/fr/mod": constant(1000.0, rows=365),
            "input/hydro/common/capacity/maxpower_fr": constant(4666.0, columns=4, rows=365),
            "input/hydro/series/de/mod": constant(500.0, rows=365),
            "input/hydro/series/de/maxHourlyGenPower": constant(2000.0),
        }
    )


@pytest.mark.parametrize("compatibility", [{}, {"hydroPmax": "daily"}])
async def test_hydro_power_is_read_in_maxpower_by_default(compatibility: dict[str, Any]) -> None:
    """
    Since 9.2 the solver still reads `maxpower_<area>` unless `hydro-pmax = hourly`: the hourly series
    are ignored, even filled (`de`), and empty ones are not an error (`fr`).
    """
    (finding,) = await check_hydro_generation_power(study(compatibility=compatibility), hydro_reader())

    assert (finding.severity, finding.objects) == ("error", ["de"])
    assert "maxpower_<area>" in finding.message
    assert "still declare" not in finding.message


async def test_hydro_power_is_read_in_hourly_series_when_hydro_pmax_is_hourly() -> None:
    data_ = study(compatibility={"hydroPmax": "hourly"})

    (finding,) = await check_hydro_generation_power(data_, hydro_reader())

    assert (finding.severity, finding.objects) == ("error", ["fr"])
    assert "maxHourlyGenPower" in finding.message
    assert "still declare 4,666 MW" in finding.message


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


async def test_renewable_series_out_of_range() -> None:
    cluster = {"enabled": True, "unitCount": 1, "nominalCapacity": 100.0, "tsInterpretation": "production-factor"}
    reader = FakeReader({"input/renewables/series/fr/wind/series": constant(80.0)})

    (finding,) = await check_renewable_series(study(renewables={"fr / wind": cluster}), reader)

    assert finding.objects == ["fr / wind (factor from 80 to 80)"]


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


def route_study(fake_api: FakeAntaresWeb) -> str:
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
    return base


@pytest.mark.parametrize("form", [{"hydroPmax": "hourly"}, None])
async def test_load_study_data_reads_the_compatibility_flags(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient, form: dict[str, Any] | None
) -> None:
    """Older Antares Web servers do not serve the compatibility form (404): the solver defaults apply."""
    base = route_study(fake_api)
    fake_api.route("GET", f"{base}/config/compatibility/form", status_code=200 if form else 404, json_body=form)

    assert (await load_study_data(api_client, STUDY_ID)).compatibility == (form or {})


async def test_check_study_tool(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    route_study(fake_api)

    report = data(await call(api_client, "check_study", {"study_id": STUDY_ID}))

    assert report["summary"] == {"error": 1, "warning": 0, "info": 1}
    assert [finding["rule"] for finding in report["findings"]] == [
        "thermal_min_stable_power",
        "unsupplied_energy_cost",
    ]
    assert "hydro_generation_power" in report["rules_skipped"]


def placeholders(template: str) -> set[str | None]:
    return {name for _, name, _, _ in Formatter().parse(template) if name}


@pytest.mark.parametrize("key", sorted(MESSAGES))
def test_every_message_of_the_rules_is_written_in_french_with_the_same_values(key: str) -> None:
    english, french = MESSAGES[key]["en"], MESSAGES[key]["fr"]

    assert french != english
    assert placeholders(french) == placeholders(english)


def study_breaking_every_quick_rule() -> StudyData:
    return study(
        name="Scenario 2040",
        general={"horizon": "2030", "firstMonth": "january", "firstJanuary": "Monday", "selectionMode": True},
        playlist={"1": {"status": True}, "2": {"status": False}},
        areas={
            "fr": {"energyCostUnsupplied": 5.0},
            "de": {"energyCostUnsupplied": 0.0},
            "helper": {"energyCostUnsupplied": 10000.0},
        },
        thermals={
            "fr / nuclear": thermal(minStablePower=2000.0, marketBidCost=1.0),
            "fr / old": thermal(enabled=False),
            "helper / free": thermal(marginalCost=0.0, marketBidCost=0.0),
        },
        storages={"fr / battery": {"enabled": True, "efficiency": 1.2, "injectionNominalCapacity": 10.0}},
        constraints=[
            {"id": "ghost", "operator": "less", "terms": [{"data": {"area": "fr", "cluster": "unknown"}}]},
            {"id": "sleeping", "operator": "less", "terms": [{"data": {"area": "fr", "cluster": "old"}}]},
            {
                "id": "loose",
                "operator": "less",
                "terms": [{"weight": 1, "data": {"area": "helper", "cluster": "free"}}],
            },
            {"id": "off", "enabled": False},
        ],
    )


def quick_findings(language: Language) -> list[Finding]:
    return [finding for check in QUICK_CHECKS for finding in check(study_breaking_every_quick_rule(), language)]


async def deep_findings(language: Language) -> list[Finding]:
    renewable = {"enabled": True, "unitCount": 1, "nominalCapacity": 100.0, "tsInterpretation": "production-factor"}
    data_ = study(
        thermals={"fr / null": thermal(), "fr / changed": thermal()},
        renewables={"fr / wind": renewable, "fr / solar": renewable},
        constraints=[{"id": "nuc_limit", "operator": "less", "group": "scenarised", "terms": []}],
        scenario_builder={"bc": {"scenarised": {"0": 1}}},
    )
    reader = FakeReader(
        {
            "input/hydro/series/fr/mod": constant(1000.0, rows=365),
            "input/thermal/series/fr/changed/series": constant(3000.0),
            "input/renewables/series/fr/solar/series": constant(80.0),
            "input/bindingconstraints/nuc_limit_lt": constant(0.0, columns=2),
        }
    )
    return [finding for check in DEEP_CHECKS for finding in await check(data_, reader, language)]


def assert_translated(french: list[Finding], english: list[Finding]) -> None:
    assert [(f.rule, f.severity, f.count) for f in french] == [(f.rule, f.severity, f.count) for f in english]
    assert [f.rule for f in french if f.message in {e.message for e in english}] == []


def test_every_quick_rule_reports_its_findings_in_french() -> None:
    english = quick_findings("en")

    assert {f.rule for f in english} == set(QUICK_RULES)
    assert_translated(quick_findings("fr"), english)


async def test_every_deep_rule_reports_its_findings_in_french() -> None:
    english = await deep_findings("en")

    assert {f.rule for f in english} == set(DEEP_RULES)
    assert_translated(await deep_findings("fr"), english)


def test_calendar_in_french_names_the_days_in_french() -> None:
    data_ = study(general={"horizon": "2030", "firstMonth": "january", "firstJanuary": "Monday"})

    (finding,) = check_calendar(data_, "fr")

    assert finding.message == (
        "Le 1er janvier est réglé sur un lundi, alors que le 1er janvier 2030 est un mardi (horizon « 2030 ») : "
        "les jours de semaine et les week-ends des séries temporelles sont décalés."
    )


def test_objects_are_described_in_french() -> None:
    data_ = study_breaking_every_quick_rule()

    assert check_playlist(data_, "fr")[0].objects == ["année 2"]
    assert check_thermal_market_bid(data_, "fr")[0].objects == ["fr / nuclear (offre 1.0 < coût 10.0 EUR/MWh)"]
    assert check_storage_efficiency(data_, "fr")[0].objects == ["fr / battery (injection 1.2, soutirage 1)"]


def test_disabled_objects_are_counted_in_french() -> None:
    messages = [finding.message for finding in check_disabled_objects(study_breaking_every_quick_rule(), "fr")]

    assert messages == ["1/3 clusters thermiques sont désactivés.", "Contraintes couplantes désactivées."]


async def test_large_numbers_are_written_the_french_way() -> None:
    """`3,000.0 MW` reads as 3 MW for a French reader."""
    data_ = study(thermals={"fr / changed": thermal(unitCount=2)}, compatibility={"hydroPmax": "hourly"})
    reader = FakeReader({"input/thermal/series/fr/changed/series": constant(3000.0)})

    (above,) = await check_thermal_availability(data_, reader, "fr")
    (hydro,) = await check_hydro_generation_power(data_, hydro_reader(), "fr")

    assert above.objects == ["fr / changed (3\u00a0000,0 > 2\u00a0000,0 MW)"]
    assert "déclarent encore 4\u00a0666 MW" in hydro.message


async def test_check_study_tool_answers_in_english_by_default(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    route_study(fake_api)

    report = data(await call(api_client, "check_study", {"study_id": STUDY_ID}))

    assert report["findings"][0]["message"] == "Min stable power above the unit capacity."


async def test_check_study_tool_answers_in_french_when_asked(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    route_study(fake_api)

    report = data(await call(api_client, "check_study", {"study_id": STUDY_ID, "language": "fr"}))

    assert report["findings"][0]["message"] == "Puissance minimale stable supérieure à la capacité d'une unité."


async def test_check_study_tool_writes_its_notes_in_french(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    route_study(fake_api)

    report = data(await call(api_client, "check_study", {"study_id": STUDY_ID, "deep": True, "language": "fr"}))

    assert [note.split(" ", 1)[1] for note in report["notes"]] == [
        "matrices n'ont pas pu être lues et n'ont pas été vérifiées."
    ]
