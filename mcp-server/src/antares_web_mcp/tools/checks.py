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
tested. The model then explains and prioritizes the findings. A finding is a *possible* issue:
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
from antares_web_mcp.tools.common import READ_ONLY, StudyId, guard, parse_version

Severity = Literal["error", "warning", "info"]
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
MAX_OBJECTS = 30
CONCURRENT_DOWNLOADS = 8
YEAR = re.compile(r"(?<!\d)(?:19|20|21)\d{2}(?!\d)")  # also in "case_2060final"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

QUICK_RULES = [
    "calendar",
    "playlist",
    "thermal_min_stable_power",
    "thermal_market_bid",
    "unsupplied_energy_cost",
    "storage_efficiency",
    "disabled_objects",
    "isolated_areas",
    "constraint_references",
    "relaxable_helper_terms",
]
DEEP_RULES = [
    "hydro_generation_power",
    "thermal_availability",
    "renewable_series",
    "link_capacities",
    "scenarised_constraints",
]


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


def finding(rule: str, severity: Severity, message: str, objects: list[str]) -> Finding:
    return Finding(rule=rule, severity=severity, message=message, objects=objects[:MAX_OBJECTS], count=len(objects))


@dataclass
class StudyData:
    """Everything the quick rules need, loaded once."""

    name: str
    version: str
    general: dict[str, Any]
    playlist: dict[str, Any] | None
    areas: dict[str, dict[str, Any]]
    links: dict[str, dict[str, Any]]
    thermals: dict[str, dict[str, Any]]
    renewables: dict[str, dict[str, Any]]
    storages: dict[str, dict[str, Any]]
    constraints: list[dict[str, Any]]
    scenario_builder: dict[str, Any] = field(default_factory=dict)

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


def check_calendar(data: StudyData) -> list[Finding]:
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

    findings = []
    if horizon_years and all(january_first(y) != weekday for y in january_years(horizon_years)):
        findings.append(
            finding(
                "calendar",
                "warning",
                f"1 January is set to a {weekday}, which does not match the horizon '{general.get('horizon')}'.",
                ["settings/generaldata.ini"],
            )
        )
    foreign = [y for y in name_years if y not in horizon_years]
    if foreign and all(january_first(y) != weekday for y in january_years(foreign)):
        matching = [y for y in sorted(january_years(horizon_years)) if january_first(y) == weekday]
        calendar = f"the {matching[0]} calendar" if matching else "another calendar"
        findings.append(
            finding(
                "calendar",
                "warning",
                f"The study name refers to {foreign[0]} (1 January {foreign[0]} is a {january_first(foreign[0])}), "
                f"but the study uses {calendar} (horizon '{general.get('horizon')}', 1 January = {weekday}). "
                "Check that time series built for that year are aligned with this calendar (weekends, holidays).",
                ["settings/generaldata.ini"],
            )
        )
    return findings


def check_playlist(data: StudyData) -> list[Finding]:
    if not data.playlist or not data.general.get("selectionMode"):
        return []
    inactive = [year for year, value in data.playlist.items() if not value.get("status")]
    if not inactive:
        return []
    return [
        finding(
            "playlist",
            "info",
            f"{len(inactive)} of {len(data.playlist)} Monte-Carlo years are excluded by the playlist.",
            [f"year {year}" for year in inactive],
        )
    ]


def check_thermal_min_stable_power(data: StudyData) -> list[Finding]:
    wrong = [
        f"{cluster_id} ({row.get('minStablePower')} > {row.get('nominalCapacity')} MW)"
        for cluster_id, row in data.thermals.items()
        if _enabled(row) and float(row.get("minStablePower", 0)) > float(row.get("nominalCapacity", 0))
    ]
    if not wrong:
        return []
    return [finding("thermal_min_stable_power", "error", "Min stable power above the unit capacity.", wrong)]


def check_thermal_market_bid(data: StudyData) -> list[Finding]:
    wrong = [
        f"{cluster_id} (bid {row.get('marketBidCost')} < cost {row.get('marginalCost')} EUR/MWh)"
        for cluster_id, row in data.thermals.items()
        if _enabled(row)
        and _capacity(row) > 0
        and float(row.get("marketBidCost", 0)) < float(row.get("marginalCost", 0))
    ]
    if not wrong:
        return []
    return [
        finding(
            "thermal_market_bid",
            "warning",
            "Market bid below the marginal cost: the merit order uses the bid, so these plants run before "
            "cheaper ones (intended only to model a subsidy or a must-run contract).",
            wrong,
        )
    ]


def check_unsupplied_energy_cost(data: StudyData) -> list[Finding]:
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
    if too_low:
        findings.append(
            finding(
                "unsupplied_energy_cost",
                "warning",
                "Unsupplied energy cost below the most expensive plant of the area: the optimiser sheds load "
                "rather than running these plants.",
                too_low,
            )
        )
    if free:
        findings.append(
            finding(
                "unsupplied_energy_cost",
                "info",
                "Unsupplied energy cost of 0: the load of these areas can be left unserved for free. Usual for "
                "technical (virtual) nodes modelling an optional consumption, an error for a real area.",
                free,
            )
        )
    return findings


def check_storage_efficiency(data: StudyData) -> list[Finding]:
    wrong = []
    for storage_id, row in data.storages.items():
        injection = float(row.get("efficiency", 1))
        withdrawal = float(row.get("efficiencyWithdrawal", 1) or 1)
        if _enabled(row) and (injection > 1 or withdrawal > 1):
            wrong.append(f"{storage_id} (injection {injection:g}, withdrawal {withdrawal:g})")
    if not wrong:
        return []
    return [
        finding(
            "storage_efficiency",
            "warning",
            "Storage efficiency above 1: the storage returns more energy than it absorbs. Check whether it "
            "compensates a loss modelled elsewhere.",
            wrong,
        )
    ]


def check_disabled_objects(data: StudyData) -> list[Finding]:
    findings = []
    for kind, table, capacity in (
        ("thermal clusters", data.thermals, _capacity),
        ("renewable clusters", data.renewables, _capacity),
        ("short-term storages", data.storages, lambda row: float(row.get("injectionNominalCapacity", 0))),
    ):
        disabled = [object_id for object_id, row in table.items() if not _enabled(row)]
        empty = [object_id for object_id, row in table.items() if _enabled(row) and capacity(row) == 0]
        if disabled:
            findings.append(
                finding("disabled_objects", "info", f"{len(disabled)}/{len(table)} {kind} are disabled.", disabled)
            )
        if empty:
            findings.append(
                finding("disabled_objects", "info", f"{len(empty)} enabled {kind} have no capacity.", empty)
            )
    disabled_constraints = [bc["id"] for bc in data.constraints if not bc.get("enabled", True)]
    if disabled_constraints:
        findings.append(finding("disabled_objects", "info", "Disabled binding constraints.", disabled_constraints))
    return findings


def check_isolated_areas(data: StudyData) -> list[Finding]:
    isolated = sorted(set(data.areas) - data.linked_areas)
    if not isolated or not data.links:
        return []
    return [
        finding(
            "isolated_areas",
            "info",
            "Areas without any link: their production only serves their own load (or is spilled). Usual for "
            "helper areas used in binding constraints.",
            isolated,
        )
    ]


def check_constraint_references(data: StudyData) -> list[Finding]:
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
    if missing:
        findings.append(
            finding("constraint_references", "error", "Binding constraint terms on objects that do not exist.", missing)
        )
    if disabled:
        findings.append(
            finding(
                "constraint_references",
                "warning",
                "Binding constraint terms on disabled clusters: their production is 0, which may make the "
                "constraint infeasible or meaningless.",
                disabled,
            )
        )
    return findings


def check_relaxable_helper_terms(data: StudyData) -> list[Finding]:
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
    if not relaxable:
        return []
    return [
        finding(
            "relaxable_helper_terms",
            "warning",
            "These constraints use a free and optional production of an isolated (helper) area on the side that "
            "is relaxed by lowering it: the optimiser can reduce it at no cost, so the constraint probably never "
            "binds. If the helper stands for an availability, it only works as an upper bound. Check in the "
            "outputs whether the helper produces less than its availability.",
            relaxable,
        )
    ]


QUICK_CHECKS: list[Callable[[StudyData], list[Finding]]] = [
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


async def check_hydro_generation_power(data: StudyData, reader: MatrixReader) -> list[Finding]:
    areas = sorted(data.areas)
    inflows = await reader.read_all([f"input/hydro/series/{area}/mod" for area in areas])
    with_inflows = [
        area
        for area, matrix in zip(areas, inflows, strict=True)
        if matrix is not None and (stats := matrix_stats(matrix)).max is not None and stats.max > 0
    ]
    if parse_version(data.version) >= (9, 2):
        powers = await reader.read_all([f"input/hydro/series/{area}/maxHourlyGenPower" for area in with_inflows])
    else:
        powers = await reader.read_all([f"input/hydro/common/capacity/maxpower_{area}" for area in with_inflows])
    # Since 9.2, the hourly series hold the generating power; before, the 1st column of maxpower_<area>.
    columns = slice(None) if parse_version(data.version) >= (9, 2) else slice(0, 1)
    blocked = [
        area
        for area, matrix in zip(with_inflows, powers, strict=True)
        if matrix is not None and matrix_stats([row[columns] for row in matrix]).all_zero
    ]
    if not blocked:
        return []
    message = "Hydro inflows but no generating power: the reservoir cannot be turbined."
    if parse_version(data.version) >= (9, 2):
        legacy = await reader.read_all([f"input/hydro/common/capacity/maxpower_{area}" for area in blocked])
        legacy_mw = sum((matrix_stats([row[:1] for row in m]).max or 0) for m in legacy if m)
        if legacy_mw > 0:
            message += (
                f" The legacy files maxpower_<area> (format before 9.2) still declare {legacy_mw:,.0f} MW in "
                "total, while 'input/hydro/series/<area>/maxHourlyGenPower' (read since 9.2) is empty: probably "
                "an incomplete version upgrade, or a study generated with the old format."
            )
    return [finding("hydro_generation_power", "error", message, blocked)]


async def check_thermal_availability(data: StudyData, reader: MatrixReader) -> list[Finding]:
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
            above.append(f"{cluster_id} ({stats.max:,.1f} > {_capacity(row):,.1f} MW)")
    findings = []
    if zero:
        findings.append(
            finding(
                "thermal_availability",
                "error",
                "Enabled clusters with a capacity but a null availability series: they never produce.",
                zero,
            )
        )
    if above:
        findings.append(
            finding(
                "thermal_availability",
                "warning",
                "Availability above the installed capacity (unit count x nominal capacity): the capacity was "
                "probably changed without updating the series.",
                above,
            )
        )
    return findings


async def check_renewable_series(data: StudyData, reader: MatrixReader) -> list[Finding]:
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
            out_of_range.append(f"{cluster_id} (factor from {stats.min:g} to {stats.max:g})")
    findings = []
    if zero:
        findings.append(finding("renewable_series", "warning", "Enabled renewable clusters with a null series.", zero))
    if out_of_range:
        findings.append(
            finding(
                "renewable_series",
                "error",
                "Production factors outside [0, 1]: the series is probably in MW while the cluster expects a "
                "production factor (or the opposite).",
                out_of_range,
            )
        )
    return findings


async def check_link_capacities(data: StudyData, reader: MatrixReader) -> list[Finding]:
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
    if not dead:
        return []
    return [
        finding(
            "link_capacities",
            "warning",
            "Links with a 0 MW capacity in both directions: they carry nothing (placeholders, or capacities "
            "never filled in).",
            dead,
        )
    ]


async def check_scenarised_constraints(data: StudyData, reader: MatrixReader) -> list[Finding]:
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
    if not useless:
        return []
    return [
        finding(
            "scenarised_constraints",
            "info",
            "Constraints of a scenarised group whose right-hand side columns are all identical: the "
            "scenarisation has no effect.",
            useless,
        )
    ]


DEEP_CHECKS: list[Callable[[StudyData, MatrixReader], Awaitable[list[Finding]]]] = [
    check_hydro_generation_power,
    check_thermal_availability,
    check_renewable_series,
    check_link_capacities,
    check_scenarised_constraints,
]


async def load_study_data(client: AntaresWebClient, study_id: str) -> StudyData:
    study = await client.get_study(study_id)
    (
        general,
        playlist,
        areas,
        links,
        thermals,
        renewables,
        storages,
        constraints,
        scenario_builder,
    ) = await asyncio.gather(
        client.get_config_form(study_id, "general"),
        optional(client.get_config_form(study_id, "playlist")),
        client.get_table(study_id, "areas"),
        client.get_table(study_id, "links"),
        client.get_table(study_id, "thermals"),
        client.get_table(study_id, "renewables"),
        client.get_table(study_id, "st-storages"),
        client.list_binding_constraints(study_id),
        optional(client.get_scenario_builder(study_id)),
    )
    return StudyData(
        name=study.get("name", ""),
        version=str(study.get("version", "")),
        general=general,
        playlist=playlist,
        areas=areas,
        links=links,
        thermals=thermals,
        renewables=renewables,
        storages=storages,
        constraints=constraints,
        scenario_builder=scenario_builder or {},
    )


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
    ) -> CheckReport:
        """
        Check the consistency of the inputs of a study with deterministic rules (calendar, costs, plant
        constraints, storages, binding constraints, helper areas, and with `deep` the time series).
        Each finding is a possible issue to explain to the user: some are deliberate modelling choices,
        which only the author of the study can confirm.
        """
        data = await guard(load_study_data(client, study_id))
        findings = [result for check in QUICK_CHECKS for result in check(data)]
        notes = []
        if deep:
            reader = MatrixReader(client, study_id)
            for index, (rule, deep_check) in enumerate(zip(DEEP_RULES, DEEP_CHECKS, strict=True)):
                # Progress notifications also keep waiting the clients that reset their timeout on progress.
                await ctx.report_progress(index, len(DEEP_CHECKS), f"Checking {rule}")
                findings += await deep_check(data, reader)
            if reader.failures:
                notes.append(f"{reader.failures} matrices could not be read and were not checked.")
        findings.sort(key=lambda item: SEVERITY_ORDER[item.severity])
        summary = {severity: sum(1 for f in findings if f.severity == severity) for severity in SEVERITY_ORDER}
        return CheckReport(
            summary=summary,
            findings=findings,
            rules_run=QUICK_RULES + (DEEP_RULES if deep else []),
            rules_skipped=[] if deep else DEEP_RULES,
            notes=notes,
        )
