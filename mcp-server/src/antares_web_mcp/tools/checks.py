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
Consistency checks of the inputs of a study (`check_study`).

Each rule is deterministic: the same study always gives the same findings, and each rule is unit
tested. A model can then explain the findings, when the user asks for it. A finding is a *possible* issue:
some are deliberate modelling choices, which only the author can confirm.

Quick rules only read the properties of the objects (table mode); "deep" rules download time
series and can take a few minutes on a large study.
"""

import asyncio
import datetime
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import Context, MCPServer
from pydantic import BaseModel, Field

from antares_web_mcp.client import AntaresWebClient, AntaresWebError
from antares_web_mcp.tools.analysis import matrix_stats, optional, rhs_paths
from antares_web_mcp.tools.check_messages import number, say, weekday_name
from antares_web_mcp.tools.common import READ_ONLY, Language, StudyId

Severity = Literal["error", "warning", "info"]
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
MAX_OBJECTS = 30
CONCURRENT_DOWNLOADS = 8
YEAR = re.compile(r"(?<!\d)(?:19|20|21)\d{2}(?!\d)")  # also in "case_2060final"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class Finding(BaseModel):
    rule: str
    severity: Severity
    message: str
    objects: list[str] = Field(description=f"Objects concerned (at most {MAX_OBJECTS} listed).")
    count: int = Field(description="Total number of objects concerned.")


class CheckReport(BaseModel):
    summary: dict[str, int] = Field(description="Number of findings by severity.")
    findings: list[Finding] = Field(description="Most severe first.")
    rules_run: list[str]
    rules_skipped: list[str] = Field(description="Deep rules, run only with `deep=true`.")
    notes: list[str]


def finding(rule: str, severity: Severity, message: str, objects: list[str]) -> list[Finding]:
    """A rule reports a finding only when some objects are concerned."""
    if not objects:
        return []
    return [Finding(rule=rule, severity=severity, message=message, objects=objects[:MAX_OBJECTS], count=len(objects))]


@dataclass
class StudyData:
    """Everything the quick rules need, loaded once."""

    name: str
    general: dict[str, Any]
    playlist: dict[str, Any] | None
    areas: dict[str, dict[str, Any]]
    links: dict[str, dict[str, Any]]
    thermals: dict[str, dict[str, Any]]
    renewables: dict[str, dict[str, Any]]
    storages: dict[str, dict[str, Any]]
    constraints: list[dict[str, Any]]
    scenario_builder: dict[str, Any] = field(default_factory=dict)
    # Compatibility flags of the solver (9.2+), e.g. {"hydroPmax": "daily"}: empty when not served.
    compatibility: dict[str, Any] = field(default_factory=dict)

    @property
    def linked_areas(self) -> set[str]:
        return {area for link_id in self.links for area in link_id.split(" / ")}


def _capacity(row: dict[str, Any]) -> float:
    return float(row.get("unitCount", 1)) * float(row.get("nominalCapacity", 0))


def _enabled(row: dict[str, Any]) -> bool:
    return bool(row.get("enabled", True))


# ----------------------------------------------------------------------
# Quick rules
# ----------------------------------------------------------------------


def january_first(year: int) -> str:
    return WEEKDAYS[datetime.date(year, 1, 1).weekday()]


def check_calendar(data: StudyData, language: Language = "en") -> list[Finding]:
    """The calendar (weekday of 1 January) must match the year the time series were built for."""
    general = data.general
    weekday = str(general.get("firstJanuary", ""))
    horizon_years = [int(y) for y in YEAR.findall(str(general.get("horizon") or ""))]
    name_years = [int(y) for y in YEAR.findall(data.name)]
    if not weekday:
        return []
    starts_in_january = str(general.get("firstMonth", "january")).lower() == "january"

    def january_years(years: list[int]) -> set[int]:
        """Years whose 1 January is simulated (a year starting in July ends in the next calendar year)."""
        return set(years) | (set() if starts_in_january or not years else {years[0] + 1})

    def day(year: int) -> str:
        return weekday_name(january_first(year), language)

    findings = []
    if horizon_years and all(january_first(y) != weekday for y in january_years(horizon_years)):
        # The expected days are given: whoever explains the finding (a model) must not have to compute them.
        expected = say("calendar.and", language).join(
            say("calendar.first_january", language, year=y, day=day(y)) for y in sorted(january_years(horizon_years))
        )
        findings += finding(
            "calendar",
            "warning",
            say(
                "calendar.horizon",
                language,
                weekday=weekday_name(weekday, language),
                expected=expected,
                horizon=general.get("horizon"),
            ),
            ["settings/generaldata.ini"],
        )
    foreign = [y for y in name_years if y not in horizon_years]
    if foreign and all(january_first(y) != weekday for y in january_years(foreign)):
        matching = [y for y in sorted(january_years(horizon_years)) if january_first(y) == weekday]
        calendar = (
            say("calendar.of_year", language, year=matching[0])
            if matching
            else say("calendar.of_another_year", language)
        )
        findings += finding(
            "calendar",
            "warning",
            say(
                "calendar.name",
                language,
                year=foreign[0],
                day=day(foreign[0]),
                calendar=calendar,
                horizon=general.get("horizon"),
                weekday=weekday_name(weekday, language),
            ),
            ["settings/generaldata.ini"],
        )
    return findings


def check_playlist(data: StudyData, language: Language = "en") -> list[Finding]:
    if not data.playlist or not data.general.get("selectionMode"):
        return []
    inactive = [year for year, value in data.playlist.items() if not value.get("status")]
    return finding(
        "playlist",
        "info",
        say("playlist", language, inactive=len(inactive), total=len(data.playlist)),
        [say("playlist.year", language, year=year) for year in inactive],
    )


def check_thermal_min_stable_power(data: StudyData, language: Language = "en") -> list[Finding]:
    wrong = [
        f"{cluster_id} ({row.get('minStablePower')} > {row.get('nominalCapacity')} MW)"
        for cluster_id, row in data.thermals.items()
        if _enabled(row) and float(row.get("minStablePower", 0)) > float(row.get("nominalCapacity", 0))
    ]
    return finding("thermal_min_stable_power", "error", say("thermal_min_stable_power", language), wrong)


def check_thermal_market_bid(data: StudyData, language: Language = "en") -> list[Finding]:
    wrong = [
        say(
            "thermal_market_bid.object",
            language,
            cluster=cluster_id,
            bid=row.get("marketBidCost"),
            cost=row.get("marginalCost"),
        )
        for cluster_id, row in data.thermals.items()
        if _enabled(row)
        and _capacity(row) > 0
        and float(row.get("marketBidCost", 0)) < float(row.get("marginalCost", 0))
    ]
    return finding("thermal_market_bid", "warning", say("thermal_market_bid", language), wrong)


def check_unsupplied_energy_cost(data: StudyData, language: Language = "en") -> list[Finding]:
    max_cost: dict[str, float] = {}
    for cluster_id, row in data.thermals.items():
        if _enabled(row) and _capacity(row) > 0:
            area = cluster_id.split(" / ")[0]
            max_cost[area] = max(max_cost.get(area, 0.0), float(row.get("marginalCost", 0)))
    free, too_low = [], []
    for area, row in data.areas.items():
        cost = float(row.get("energyCostUnsupplied", 0))
        if cost == 0:
            free.append(area)
        elif cost < max_cost.get(area, 0.0):
            too_low.append(f"{area} ({cost:g} < {max_cost[area]:g} EUR/MWh)")
    findings = []
    findings += finding("unsupplied_energy_cost", "warning", say("unsupplied_energy_cost.too_low", language), too_low)
    findings += finding("unsupplied_energy_cost", "info", say("unsupplied_energy_cost.free", language), free)
    return findings


def check_storage_efficiency(data: StudyData, language: Language = "en") -> list[Finding]:
    wrong = []
    for storage_id, row in data.storages.items():
        injection = float(row.get("efficiency", 1))
        withdrawal = float(row.get("efficiencyWithdrawal", 1) or 1)
        if _enabled(row) and (injection > 1 or withdrawal > 1):
            wrong.append(
                say(
                    "storage_efficiency.object",
                    language,
                    storage=storage_id,
                    injection=injection,
                    withdrawal=withdrawal,
                )
            )
    return finding("storage_efficiency", "warning", say("storage_efficiency", language), wrong)


def check_disabled_objects(data: StudyData, language: Language = "en") -> list[Finding]:
    findings = []
    for kind_key, table, capacity in (
        ("kind.thermals", data.thermals, _capacity),
        ("kind.renewables", data.renewables, _capacity),
        ("kind.storages", data.storages, lambda row: float(row.get("injectionNominalCapacity", 0))),
    ):
        kind = say(kind_key, language)
        disabled = [object_id for object_id, row in table.items() if not _enabled(row)]
        empty = [object_id for object_id, row in table.items() if _enabled(row) and capacity(row) == 0]
        findings += finding(
            "disabled_objects",
            "info",
            say("disabled_objects.disabled", language, count=len(disabled), total=len(table), kind=kind),
            disabled,
        )
        findings += finding(
            "disabled_objects",
            "info",
            say("disabled_objects.without_capacity", language, count=len(empty), kind=kind),
            empty,
        )
    disabled_constraints = [bc["id"] for bc in data.constraints if not bc.get("enabled", True)]
    findings += finding("disabled_objects", "info", say("disabled_objects.constraints", language), disabled_constraints)
    return findings


def check_isolated_areas(data: StudyData, language: Language = "en") -> list[Finding]:
    isolated = sorted(set(data.areas) - data.linked_areas)
    if not data.links:
        return []
    return finding("isolated_areas", "info", say("isolated_areas", language), isolated)


def check_constraint_references(data: StudyData, language: Language = "en") -> list[Finding]:
    clusters = {cluster_id.replace(" / ", "."): row for cluster_id, row in {**data.thermals, **data.renewables}.items()}
    missing, disabled = [], []
    for bc in data.constraints:
        if not bc.get("enabled", True):
            continue
        for term in bc.get("terms") or []:
            target = term.get("data") or {}
            if "cluster" in target:
                key = f"{target.get('area')}.{target['cluster']}"
                if key not in clusters:
                    missing.append(f"{bc['id']}: {key}")
                elif not _enabled(clusters[key]):
                    disabled.append(f"{bc['id']}: {key}")
            elif "area1" in target and f"{target['area1']} / {target.get('area2')}" not in data.links:
                missing.append(f"{bc['id']}: {target['area1']} / {target.get('area2')}")
    findings = []
    findings += finding("constraint_references", "error", say("constraint_references.missing", language), missing)
    findings += finding("constraint_references", "warning", say("constraint_references.disabled", language), disabled)
    return findings


def check_relaxable_helper_terms(data: StudyData, language: Language = "en") -> list[Finding]:
    """
    A free (zero cost), optional (no must-run, no min stable power) production in an isolated area is a
    common trick to read an availability in a binding constraint. But its production can be lowered at no
    cost: a constraint side that is relaxed by lowering it never binds.
    """
    isolated = set(data.areas) - data.linked_areas
    helpers = {
        cluster_id.replace(" / ", ".")
        for cluster_id, row in data.thermals.items()
        if _enabled(row)
        and cluster_id.split(" / ")[0] in isolated
        and float(row.get("marginalCost", 0)) == 0
        and not row.get("mustRun")
        and float(row.get("minStablePower", 0)) == 0
    }
    relaxable = []
    for bc in data.constraints:
        operator = bc.get("operator")
        if not bc.get("enabled", True) or operator not in ("less", "greater", "both"):
            continue
        for term in bc.get("terms") or []:
            target = term.get("data") or {}
            key = f"{target.get('area')}.{target.get('cluster')}"
            weight = float(term.get("weight", 1))
            lowering_relaxes = (operator in ("greater", "both") and weight < 0) or (
                operator in ("less", "both") and weight > 0
            )
            if key in helpers and lowering_relaxes:
                relaxable.append(f"{bc['id']} ({operator}, {weight:g} x {key})")
                break
    return finding("relaxable_helper_terms", "warning", say("relaxable_helper_terms", language), relaxable)


QUICK_CHECKS: list[Callable[[StudyData, Language], list[Finding]]] = [
    check_calendar,
    check_playlist,
    check_thermal_min_stable_power,
    check_thermal_market_bid,
    check_unsupplied_energy_cost,
    check_storage_efficiency,
    check_disabled_objects,
    check_isolated_areas,
    check_constraint_references,
    check_relaxable_helper_terms,
]
QUICK_RULES = [check.__name__.removeprefix("check_") for check in QUICK_CHECKS]


# ----------------------------------------------------------------------
# Deep rules (time series)
# ----------------------------------------------------------------------


class MatrixReader:
    """Downloads matrices with a bounded concurrency, counting those that cannot be read."""

    def __init__(self, client: AntaresWebClient, study_id: str) -> None:
        self.client = client
        self.study_id = study_id
        self.failures = 0
        self._semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)

    async def read(self, path: str) -> list[list[float]] | None:
        async with self._semaphore:
            try:
                return await self.client.get_matrix(self.study_id, path)
            except AntaresWebError:
                self.failures += 1
                return None

    async def read_all(self, paths: list[str]) -> list[list[list[float]] | None]:
        return list(await asyncio.gather(*(self.read(path) for path in paths)))


async def check_hydro_generation_power(
    data: StudyData, reader: MatrixReader, language: Language = "en"
) -> list[Finding]:
    areas = sorted(data.areas)
    inflows = await reader.read_all([f"input/hydro/series/{area}/mod" for area in areas])
    with_inflows = [
        area
        for area, matrix in zip(areas, inflows, strict=True)
        if matrix is not None and (stats := matrix_stats(matrix)).max is not None and stats.max > 0
    ]
    # The solver reads the 1st column of maxpower_<area>, unless the compatibility flag `hydro-pmax` (9.2+)
    # is `hourly`: only then are the hourly series read. The version alone does not tell which file is used.
    hourly = str(data.compatibility.get("hydroPmax", "daily")).lower() == "hourly"
    if hourly:
        powers = await reader.read_all([f"input/hydro/series/{area}/maxHourlyGenPower" for area in with_inflows])
    else:
        powers = await reader.read_all([f"input/hydro/common/capacity/maxpower_{area}" for area in with_inflows])
    columns = slice(None) if hourly else slice(0, 1)
    blocked = [
        area
        for area, matrix in zip(with_inflows, powers, strict=True)
        if matrix is not None and matrix_stats([row[columns] for row in matrix]).all_zero
    ]
    if not blocked:
        return []
    message = say("hydro_generation_power", language)
    if hourly:
        message += say("hydro_generation_power.hourly", language)
        legacy = await reader.read_all([f"input/hydro/common/capacity/maxpower_{area}" for area in blocked])
        legacy_mw = sum((matrix_stats([row[:1] for row in m]).max or 0) for m in legacy if m)
        if legacy_mw > 0:
            message += say("hydro_generation_power.legacy", language, power=number(legacy_mw, language))
    else:
        message += say("hydro_generation_power.daily", language)
    return finding("hydro_generation_power", "error", message, blocked)


async def check_thermal_availability(data: StudyData, reader: MatrixReader, language: Language = "en") -> list[Finding]:
    clusters = [
        (cluster_id, row)
        for cluster_id, row in data.thermals.items()
        if _enabled(row) and _capacity(row) > 0 and row.get("genTs") != "force generation"
    ]
    paths = [f"input/thermal/series/{cid.split(' / ')[0]}/{cid.split(' / ')[1]}/series" for cid, _ in clusters]
    matrices = await reader.read_all(paths)
    zero, above = [], []
    for (cluster_id, row), matrix in zip(clusters, matrices, strict=True):
        if matrix is None:
            continue
        stats = matrix_stats(matrix)
        if stats.all_zero:
            zero.append(cluster_id)
        # Series are often rounded to the MW while capacities have decimals: tolerate 1 MW (or 0.1 %).
        elif stats.max is not None and stats.max > _capacity(row) + max(1.0, 0.001 * _capacity(row)):
            availability, capacity = number(stats.max, language, 1), number(_capacity(row), language, 1)
            above.append(f"{cluster_id} ({availability} > {capacity} MW)")
    findings = []
    findings += finding("thermal_availability", "error", say("thermal_availability.null", language), zero)
    findings += finding("thermal_availability", "warning", say("thermal_availability.above_capacity", language), above)
    return findings


async def check_renewable_series(data: StudyData, reader: MatrixReader, language: Language = "en") -> list[Finding]:
    clusters = [(cid, row) for cid, row in data.renewables.items() if _enabled(row) and _capacity(row) > 0]
    paths = [f"input/renewables/series/{cid.split(' / ')[0]}/{cid.split(' / ')[1]}/series" for cid, _ in clusters]
    matrices = await reader.read_all(paths)
    zero, out_of_range = [], []
    for (cluster_id, row), matrix in zip(clusters, matrices, strict=True):
        if matrix is None:
            continue
        stats = matrix_stats(matrix)
        if stats.all_zero:
            zero.append(cluster_id)
        elif row.get("tsInterpretation") == "production-factor" and ((stats.max or 0) > 1.0001 or (stats.min or 0) < 0):
            out_of_range.append(
                say("renewable_series.object", language, cluster=cluster_id, minimum=stats.min, maximum=stats.max)
            )
    findings = []
    findings += finding("renewable_series", "warning", say("renewable_series.null", language), zero)
    findings += finding("renewable_series", "error", say("renewable_series.out_of_range", language), out_of_range)
    return findings


async def check_link_capacities(data: StudyData, reader: MatrixReader, language: Language = "en") -> list[Finding]:
    links = [
        link_id for link_id, row in data.links.items() if row.get("transmissionCapacities", "enabled") == "enabled"
    ]
    paths = []
    for link_id in links:
        area1, area2 = link_id.split(" / ")
        paths += [f"input/links/{area1}/capacities/{area2}_direct", f"input/links/{area1}/capacities/{area2}_indirect"]
    matrices = await reader.read_all(paths)
    dead = [
        link_id
        for index, link_id in enumerate(links)
        if (direct := matrices[2 * index]) is not None
        and (indirect := matrices[2 * index + 1]) is not None
        and matrix_stats(direct).all_zero
        and matrix_stats(indirect).all_zero
    ]
    return finding("link_capacities", "warning", say("link_capacities", language), dead)


async def check_scenarised_constraints(
    data: StudyData, reader: MatrixReader, language: Language = "en"
) -> list[Finding]:
    groups = set((data.scenario_builder.get("bc") or {}).keys())
    constraints = [bc for bc in data.constraints if bc.get("group") in groups]
    paths = [path for bc in constraints for path in rhs_paths(bc["id"], bc.get("operator", ""))]
    matrices = await reader.read_all(paths)
    useless = sorted(
        {
            path.rsplit("/", 1)[1].rsplit("_", 1)[0]
            for path, matrix in zip(paths, matrices, strict=True)
            if matrix is not None and (stats := matrix_stats(matrix)).columns > 1 and stats.identical_columns
        }
    )
    return finding("scenarised_constraints", "info", say("scenarised_constraints", language), useless)


DEEP_CHECKS: list[Callable[[StudyData, MatrixReader, Language], Awaitable[list[Finding]]]] = [
    check_hydro_generation_power,
    check_thermal_availability,
    check_renewable_series,
    check_link_capacities,
    check_scenarised_constraints,
]
DEEP_RULES = [check.__name__.removeprefix("check_") for check in DEEP_CHECKS]


async def load_study_data(client: AntaresWebClient, study_id: str) -> StudyData:
    study = await client.get_study(study_id)
    sources = {
        "general": client.get_config_form(study_id, "general"),
        "playlist": optional(client.get_config_form(study_id, "playlist")),
        "areas": client.get_table(study_id, "areas"),
        "links": client.get_table(study_id, "links"),
        "thermals": client.get_table(study_id, "thermals"),
        "renewables": client.get_table(study_id, "renewables"),
        "storages": client.get_table(study_id, "st-storages"),
        "constraints": client.list_binding_constraints(study_id),
        "scenario_builder": optional(client.get_scenario_builder(study_id)),
        "compatibility": optional(client.get_config_form(study_id, "compatibility")),
    }
    values: dict[str, Any] = dict(zip(sources, await asyncio.gather(*sources.values()), strict=True))
    values["scenario_builder"] = values["scenario_builder"] or {}
    values["compatibility"] = values["compatibility"] or {}
    return StudyData(name=study.get("name", ""), **values)


def register(mcp: MCPServer, client: AntaresWebClient) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def check_study(
        study_id: StudyId,
        ctx: Context[Any, Any],
        deep: Annotated[
            bool,
            Field(
                description=(
                    "Also check the time series (hydro power, thermal availability, renewable factors, link "
                    "capacities, scenarised constraints). Downloads many matrices: can take minutes."
                )
            ),
        ] = False,
        language: Annotated[
            Language, Field(description="Language of the messages of the findings and of the notes.")
        ] = "en",
    ) -> CheckReport:
        """
        Check the consistency of the inputs of a study with deterministic rules (calendar, costs, plant
        constraints, storages, binding constraints, helper areas, and with `deep` the time series).
        Each finding is a possible issue to explain to the user: some are deliberate modelling choices,
        which only the author of the study can confirm.
        """
        data = await load_study_data(client, study_id)
        findings = [result for check in QUICK_CHECKS for result in check(data, language)]
        notes = []
        if deep:
            reader = MatrixReader(client, study_id)
            for index, (rule, deep_check) in enumerate(zip(DEEP_RULES, DEEP_CHECKS, strict=True)):
                # Progress notifications also keep waiting the clients that reset their timeout on progress.
                await ctx.report_progress(index, len(DEEP_CHECKS), f"Checking {rule}")
                findings += await deep_check(data, reader, language)
            if reader.failures:
                notes.append(say("note.unreadable_matrices", language, count=reader.failures))
        findings.sort(key=lambda item: SEVERITY_ORDER[item.severity])
        summary = {severity: sum(1 for f in findings if f.severity == severity) for severity in SEVERITY_ORDER}
        return CheckReport(
            summary=summary,
            findings=findings,
            rules_run=QUICK_RULES + (DEEP_RULES if deep else []),
            rules_skipped=[] if deep else DEEP_RULES,
            notes=notes,
        )
