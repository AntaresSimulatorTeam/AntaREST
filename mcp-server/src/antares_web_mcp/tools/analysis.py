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
Tools to understand the inputs of a study: what it models and why it is set up that way.

An industrial study has hundreds of objects and matrices of 8760 x 1000 values: these tools
return summaries (patterns, totals, statistics), never raw matrices, so that the model can
reason on a whole study within its context window.
"""

import asyncio
import html
import json
import re
from collections import Counter, defaultdict
from collections.abc import Awaitable, Iterator
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from antares_web_mcp.client import AntaresWebClient, AntaresWebError
from antares_web_mcp.tools.common import READ_ONLY, AreaId, StudyId, guard

TableKind = Literal["areas", "links", "thermals", "renewables", "st-storages", "binding-constraints"]

SCENARIO_RULES = {
    "l": "load",
    "h": "hydro inflows",
    "w": "wind (aggregated)",
    "s": "solar (aggregated)",
    "t": "thermal clusters availability",
    "r": "renewable clusters",
    "ntc": "link capacities",
    "bc": "binding constraint groups",
    "hl": "hydro initial levels",
    "hfl": "hydro final levels",
    "hgp": "hydro generation power",
    "sts": "short-term storage inflows",
    "sta": "short-term storage additional constraints",
}
MAX_LISTED_FILES = 200
WX_TAG = re.compile(r"<[^>]+>")
SPACES = re.compile(r"[ \t]+")


# ----------------------------------------------------------------------
# Pure helpers (unit tested)
# ----------------------------------------------------------------------


def comments_to_text(comments: str) -> str:
    """Study comments are rich text written by Antares Simulator desktop (wxWidgets XML): keep the text."""
    if "<richtext" not in comments and "<?xml" not in comments:
        return comments.strip()
    text = html.unescape(WX_TAG.sub("\n", comments))
    lines = (SPACES.sub(" ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


class ColumnSums(BaseModel):
    mean: float
    min: float
    max: float


class MatrixStats(BaseModel):
    rows: int
    columns: int = Field(description="Number of time series (Monte-Carlo scenarios) of the matrix.")
    min: float | None
    max: float | None
    mean: float | None
    all_zero: bool = Field(description="True for an empty matrix (Antares Web then uses default zeros).")
    constant: bool = Field(description="Every cell has the same value.")
    identical_columns: bool = Field(description="All time series are identical (no variability between scenarios).")
    column_sums: ColumnSums | None = Field(
        description="Sum of each column over its rows: for an hourly series in MW, the annual energy in MWh."
    )


def matrix_stats(data: list[list[float]]) -> MatrixStats:
    columns = list(zip(*data)) if data else []
    if not columns or not columns[0]:
        return MatrixStats(
            rows=len(data),
            columns=len(columns),
            min=None,
            max=None,
            mean=None,
            all_zero=True,
            constant=True,
            identical_columns=True,
            column_sums=None,
        )
    sums = [float(sum(column)) for column in columns]
    minimum = float(min(min(column) for column in columns))
    maximum = float(max(max(column) for column in columns))
    cells = len(columns) * len(columns[0])
    return MatrixStats(
        rows=len(data),
        columns=len(columns),
        min=minimum,
        max=maximum,
        mean=sum(sums) / cells,
        all_zero=minimum == 0 == maximum,
        constant=minimum == maximum,
        identical_columns=all(column == columns[0] for column in columns[1:]),
        column_sums=ColumnSums(mean=sum(sums) / len(sums), min=min(sums), max=max(sums)),
    )


def scenario_leaves(node: dict[str, Any], prefix: str = "") -> Iterator[tuple[str, dict[str, Any]]]:
    """
    Yields ``(object, {year: series})`` for each object of a scenario builder rule. Objects are nested
    (``area``, ``area / cluster`` or ``link``); a mapping of Monte-Carlo years has digit keys ("0", "1"...).
    """
    if node and all(key.isdigit() for key in node):
        yield prefix, node
        return
    for key, value in node.items():
        if isinstance(value, dict):
            yield from scenario_leaves(value, f"{prefix} / {key}" if prefix else key)


def year_sequence(mapping: dict[str, Any], nb_years: int) -> tuple[Any, ...]:
    """Series used for each Monte-Carlo year, in year order ("" = random draw)."""
    return tuple(mapping.get(str(year), "") for year in range(nb_years))


def describe_sequence(sequence: tuple[Any, ...]) -> str:
    """Human-readable pattern of the series used for each Monte-Carlo year."""
    values = [value for value in sequence if value != ""]
    if not values:
        return "random draw every year"
    random_years = len(sequence) - len(values)
    suffix = f" ({random_years} years drawn at random)" if random_years else ""
    distinct = set(values)
    if len(distinct) == 1:
        return f"always {values[0]}{suffix}"
    if not random_years and all(isinstance(value, int) for value in values):
        period = max(values)
        if all(value == year % period + 1 for year, value in enumerate(values)):
            return f"cycle over series 1 to {period} (year y uses series y mod {period} + 1)"
    return f"custom mapping over {len(distinct)} distinct values{suffix}"


class MappingGroup(BaseModel):
    pattern: str
    objects: int = Field(description="Number of objects sharing exactly this year -> series mapping.")
    examples: list[str]
    same_as_load: bool = Field(
        description="Same mapping as most load areas: these series are drawn from the same (climatic) scenario."
    )


class ScenarioRule(BaseModel):
    symbol: str
    meaning: str
    objects: int
    groups: list[MappingGroup] = Field(description="Objects grouped by identical mapping, largest first (at most 5).")


class MonteCarloDesign(BaseModel):
    nb_years: int
    building_mode: str = Field(description="'Custom' when the scenario builder below is used, else automatic draws.")
    active_years: int = Field(description="Years selected in the playlist.")
    rules: list[ScenarioRule]
    distinct_scenarios: int = Field(
        description="Number of distinct combinations of series over all rules: the actual number of different years."
    )
    notes: list[str]


def summarize_scenario_builder(rules: dict[str, Any], nb_years: int) -> tuple[list[ScenarioRule], int, list[str]]:
    sequences: dict[str, dict[str, tuple[Any, ...]]] = {
        symbol: {name: year_sequence(mapping, nb_years) for name, mapping in scenario_leaves(content)}
        for symbol, content in rules.items()
        if isinstance(content, dict)
    }
    load_counts = Counter(sequences.get("l", {}).values())
    reference = load_counts.most_common(1)[0][0] if load_counts else None

    summaries: list[ScenarioRule] = []
    notes: list[str] = []
    for symbol, objects in sequences.items():
        if not objects:
            continue
        by_sequence: dict[tuple[Any, ...], list[str]] = defaultdict(list)
        for name, sequence in objects.items():
            by_sequence[sequence].append(name)
        groups = sorted(by_sequence.items(), key=lambda item: -len(item[1]))
        summaries.append(
            ScenarioRule(
                symbol=symbol,
                meaning=SCENARIO_RULES.get(symbol, symbol),
                objects=len(objects),
                groups=[
                    MappingGroup(
                        pattern=describe_sequence(sequence),
                        objects=len(names),
                        examples=names[:5],
                        same_as_load=sequence == reference,
                    )
                    for sequence, names in groups[:5]
                ],
            )
        )
        if reference is not None and symbol != "l":
            synchronized = sum(len(names) for sequence, names in groups if sequence == reference)
            if synchronized:
                notes.append(
                    f"{synchronized}/{len(objects)} objects of rule '{symbol}' ({SCENARIO_RULES.get(symbol, symbol)}) "
                    "use the same series as the load: they are drawn from the same scenario (e.g. climatic year)."
                )
    if reference is not None and len(load_counts) == 1:
        notes.insert(
            0, f"All {load_counts[reference]} load areas share the same mapping: {describe_sequence(reference)}."
        )

    all_sequences = [sequence for objects in sequences.values() for sequence in objects.values()]
    distinct = len({tuple(sequence[year] for sequence in all_sequences) for year in range(nb_years)}) if nb_years else 0
    return summaries, distinct, notes


def flatten_tree(tree: Any, prefix: str) -> list[str]:
    """Paths of the files of a folder listing returned by Antares Web (folders are dictionaries)."""
    if not isinstance(tree, dict):
        return [prefix]
    paths: list[str] = []
    for name, child in tree.items():
        path = f"{prefix}/{name}"
        paths.extend(flatten_tree(child, path) if isinstance(child, dict) and child else [path])
    return paths


def term_label(term: dict[str, Any]) -> str:
    data = term.get("data") or {}
    weight = term.get("weight", 1.0)
    offset = term.get("offset")
    if "cluster" in data:
        target = f"{data.get('area')}.{data['cluster']}"
    elif "area1" in data:
        target = f"flow({data['area1']} -> {data.get('area2')})"
    else:
        target = json.dumps(data)
    return f"{weight:g} x {target}" + (f" [offset {offset}h]" if offset else "")


def rhs_paths(constraint_id: str, operator: str) -> list[str]:
    suffixes = {"less": ["lt"], "greater": ["gt"], "equal": ["eq"], "both": ["lt", "gt"]}
    return [f"input/bindingconstraints/{constraint_id}_{suffix}" for suffix in suffixes.get(operator, [])]


def row_area_ids(kind: str, row_id: str) -> set[str]:
    """Areas a table-mode row belongs to: ``fr``, ``de / fr`` (links) or ``fr / nuclear`` (clusters)."""
    parts = [part.strip() for part in row_id.split(" / ")]
    if kind == "links":
        return set(parts)
    return {parts[0]} if kind != "binding-constraints" else set()


# ----------------------------------------------------------------------
# Tool results
# ----------------------------------------------------------------------


class StudyContext(BaseModel):
    id: str
    name: str
    version: str
    type: str = Field(description="'rawstudy' or 'variantstudy'.")
    author: str | None
    horizon: str | None
    tags: list[str]
    created: str | None
    updated: str | None
    comments: str = Field(description="Comments of the study, as plain text.")
    parents: list[str] = Field(description="For a variant: its ancestors, from the direct parent to the root study.")
    variant_changes: list[str] | None = Field(
        description="For a variant: its commands, i.e. what it changes compared to its parent (matrices as ids)."
    )
    output_aggregations: list[str] = Field(description="Districts (sets of areas whose results are aggregated).")
    user_files: list[str] = Field(description="Files of the user/ folder: notes, scripts, reports of the author.")
    log_files: list[str]


class PlaylistSummary(BaseModel):
    active_years: int
    inactive_years: list[int] = Field(description="Inactive Monte-Carlo years (at most 50 listed).")
    weighted_years: int = Field(description="Number of active years with a weight different from 1.")


class SimulationConfiguration(BaseModel):
    general: dict[str, Any]
    optimization: dict[str, Any] | None
    advanced_parameters: dict[str, Any] | None
    adequacy_patch: dict[str, Any] | None
    playlist: PlaylistSummary | None
    disabled_output_variables: list[str] | None = Field(
        description="Output variables removed by the thematic trimming (null when the trimming is off)."
    )


class TableResult(BaseModel):
    kind: str
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    truncated: bool


class StorageCapacity(BaseModel):
    injection_mw: float
    withdrawal_mw: float
    reservoir_mwh: float


class AreaCapacity(BaseModel):
    area: str
    thermal_mw: dict[str, float] = Field(description="Installed capacity of the enabled thermal clusters, by group.")
    renewable_mw: dict[str, float] = Field(description="Installed capacity of the enabled renewable clusters.")
    storage: dict[str, StorageCapacity] = Field(description="Enabled short-term storages, by group.")


class CapacitySummary(BaseModel):
    areas: list[AreaCapacity] = Field(description="Areas with some capacity, largest first.")
    thermal_mw_by_group: dict[str, float]
    renewable_mw_by_group: dict[str, float]
    storage_by_group: dict[str, StorageCapacity]
    disabled_objects: dict[str, int] = Field(description="Number of disabled clusters / storages, by kind.")
    enabled_without_capacity: dict[str, int] = Field(description="Enabled clusters / storages with 0 MW, by kind.")


class BindingConstraintSummary(BaseModel):
    id: str
    name: str
    enabled: bool
    time_step: str
    operator: str = Field(description="'less' (<=), 'greater' (>=), 'equal' or 'both'.")
    group: str | None
    comments: str
    terms: list[str] = Field(description="'weight x cluster' or 'weight x flow(area1 -> area2)'.")
    rhs_matrices: list[str] = Field(description="Paths of the right-hand side matrices (see `get_matrix_stats`).")


class BindingConstraints(BaseModel):
    total: int
    returned: int
    constraints: list[BindingConstraintSummary]


class FileExcerpt(BaseModel):
    path: str
    total_lines: int
    matching_lines: int
    lines: list[str]
    truncated: bool


def _rounded(values: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 1) for key, value in sorted(values.items(), key=lambda item: -item[1]) if value}


async def optional(awaitable: Awaitable[Any]) -> Any:
    """Settings forms that do not exist for the study version are reported as ``None``."""
    try:
        return await awaitable
    except AntaresWebError:
        return None


def register(mcp: MCPServer, client: AntaresWebClient) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_study_context(study_id: StudyId) -> StudyContext:
        """
        Get what documents a study: metadata, comments, lineage, for a variant its changes compared to
        its parent (the hypothesis it tests), the output aggregations (districts) and the files of the
        `user/` and `logs/` folders (notes, reports, generation logs of the author, see `read_study_file`).
        Start any analysis of a study with this tool.
        """
        study = await guard(client.get_study(study_id))
        comments, parents, districts, user_tree, logs_tree = await asyncio.gather(
            optional(client.get_comments(study_id)),
            optional(client.get_parents(study_id)),
            optional(client.list_districts(study_id)),
            optional(client.get_raw(study_id, "user", depth=10)),
            optional(client.get_raw(study_id, "logs", depth=2)),
        )
        changes: list[str] | None = None
        if study.get("type") == "variantstudy":
            commands = await guard(client.list_commands(study_id))
            changes = [f"{command['action']}: {json.dumps(command.get('args'))[:400]}" for command in commands]
        user_files = flatten_tree(user_tree, "user") if user_tree else []
        return StudyContext(
            id=study["id"],
            name=study["name"],
            version=str(study.get("version", "")),
            type=study.get("type", ""),
            author=study.get("author"),
            horizon=study.get("horizon"),
            tags=study.get("tags") or [],
            created=study.get("created"),
            updated=study.get("updated"),
            comments=comments_to_text(comments or ""),
            parents=[f"{parent['name']} ({parent['id']})" for parent in parents or []],
            variant_changes=changes,
            output_aggregations=[
                f"{district['id']}: {len(district.get('areas') or [])} areas"
                + ("" if district.get("output", True) else " (no output)")
                for district in districts or []
            ],
            user_files=user_files[:MAX_LISTED_FILES],
            log_files=flatten_tree(logs_tree, "logs") if logs_tree else [],
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_study_configuration(study_id: StudyId) -> SimulationConfiguration:
        """
        Get all the simulation settings of a study in one call: general settings (mode, Monte-Carlo
        years, calendar), optimization preferences, advanced parameters, adequacy patch, playlist and
        the output variables removed by the thematic trimming. Settings that differ from the defaults
        are deliberate choices of the author: explain what each one implies.
        """
        general = await guard(client.get_config_form(study_id, "general"))
        optimization, advanced, adequacy, playlist, trimming = await asyncio.gather(
            optional(client.get_config_form(study_id, "optimization")),
            optional(client.get_config_form(study_id, "advancedparameters")),
            optional(client.get_config_form(study_id, "adequacypatch")),
            optional(client.get_config_form(study_id, "playlist")),
            optional(client.get_config_form(study_id, "thematictrimming")),
        )
        playlist_summary = None
        if isinstance(playlist, dict):
            years = {int(year): value for year, value in playlist.items()}
            active = [year for year, value in years.items() if value.get("status")]
            playlist_summary = PlaylistSummary(
                active_years=len(active),
                inactive_years=sorted(year for year in years if year not in active)[:50],
                weighted_years=sum(1 for year in active if years[year].get("weight", 1) != 1),
            )
        disabled = None
        if general.get("thematicTrimming") and isinstance(trimming, dict):
            disabled = sorted(name for name, enabled in trimming.items() if enabled is False)
        return SimulationConfiguration(
            general=general,
            optimization=optimization,
            advanced_parameters=advanced,
            adequacy_patch=adequacy,
            playlist=playlist_summary,
            disabled_output_variables=disabled,
        )

    @mcp.tool(annotations=READ_ONLY)
    async def describe_monte_carlo_scenarios(study_id: StudyId) -> MonteCarloDesign:
        """
        Explain the Monte-Carlo design of a study from its scenario builder: for each kind of time series
        (load, hydro, renewables, thermal availability, link capacities, binding constraints...), which
        series each year uses, which objects are drawn together (e.g. the same climatic year everywhere)
        and how many really distinct years are simulated.
        """
        general = await guard(client.get_config_form(study_id, "general"))
        nb_years = int(general.get("nbYears") or 0)
        rules, playlist = await asyncio.gather(
            guard(client.get_scenario_builder(study_id)), optional(client.get_config_form(study_id, "playlist"))
        )
        summaries, distinct, notes = summarize_scenario_builder(rules or {}, nb_years)
        active = (
            sum(1 for value in playlist.values() if value.get("status")) if isinstance(playlist, dict) else nb_years
        )
        if general.get("buildingMode") != "Custom":
            notes.insert(0, "The scenario builder is not used: series are drawn at random for each year.")
        return MonteCarloDesign(
            nb_years=nb_years,
            building_mode=str(general.get("buildingMode", "")),
            active_years=active,
            rules=summaries,
            distinct_scenarios=distinct if summaries else nb_years,
            notes=notes,
        )

    @mcp.tool(annotations=READ_ONLY)
    async def summarize_installed_capacity(
        study_id: StudyId,
        area_ids: Annotated[list[str] | None, Field(description="Restrict to these areas (default: all).")] = None,
    ) -> CapacitySummary:
        """
        Installed capacities of a study, by area and by group: thermal clusters (MW), renewable clusters (MW)
        and short-term storages (MW, MWh), counting enabled objects only. Also counts the disabled objects
        and the enabled ones without capacity (often placeholders).
        """
        thermals, renewables, storages = await asyncio.gather(
            guard(client.get_table(study_id, "thermals")),
            guard(client.get_table(study_id, "renewables")),
            guard(client.get_table(study_id, "st-storages")),
        )
        wanted = set(area_ids) if area_ids else None
        per_area: dict[str, AreaCapacity] = {}
        disabled: Counter[str] = Counter()
        empty: Counter[str] = Counter()

        def area_of(row_id: str) -> AreaCapacity | None:
            area = row_id.split(" / ")[0]
            if wanted is not None and area not in wanted:
                return None
            return per_area.setdefault(area, AreaCapacity(area=area, thermal_mw={}, renewable_mw={}, storage={}))

        for kind, table in (("thermal", thermals), ("renewable", renewables)):
            for row_id, row in table.items():
                if (entry := area_of(row_id)) is None:
                    continue
                if not row.get("enabled", True):
                    disabled[kind] += 1
                    continue
                capacity = float(row.get("unitCount", 1)) * float(row.get("nominalCapacity", 0))
                if not capacity:
                    empty[kind] += 1
                values = entry.thermal_mw if kind == "thermal" else entry.renewable_mw
                group = str(row.get("group", ""))
                values[group] = values.get(group, 0.0) + capacity
        for row_id, row in storages.items():
            if (entry := area_of(row_id)) is None:
                continue
            if not row.get("enabled", True):
                disabled["storage"] += 1
                continue
            if not row.get("injectionNominalCapacity") and not row.get("withdrawalNominalCapacity"):
                empty["storage"] += 1
            group = str(row.get("group", ""))
            current = entry.storage.get(group, StorageCapacity(injection_mw=0, withdrawal_mw=0, reservoir_mwh=0))
            entry.storage[group] = StorageCapacity(
                injection_mw=current.injection_mw + float(row.get("injectionNominalCapacity", 0)),
                withdrawal_mw=current.withdrawal_mw + float(row.get("withdrawalNominalCapacity", 0)),
                reservoir_mwh=current.reservoir_mwh + float(row.get("reservoirCapacity", 0)),
            )

        thermal_total: dict[str, float] = defaultdict(float)
        renewable_total: dict[str, float] = defaultdict(float)
        storage_total: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
        for entry in per_area.values():
            for group, value in entry.thermal_mw.items():
                thermal_total[group] += value
            for group, value in entry.renewable_mw.items():
                renewable_total[group] += value
            for group, storage in entry.storage.items():
                totals = storage_total[group]
                totals[0] += storage.injection_mw
                totals[1] += storage.withdrawal_mw
                totals[2] += storage.reservoir_mwh
            entry.thermal_mw = _rounded(entry.thermal_mw)
            entry.renewable_mw = _rounded(entry.renewable_mw)
        areas = [entry for entry in per_area.values() if entry.thermal_mw or entry.renewable_mw or entry.storage]
        areas.sort(key=lambda entry: -(sum(entry.thermal_mw.values()) + sum(entry.renewable_mw.values())))
        return CapacitySummary(
            areas=areas,
            thermal_mw_by_group=_rounded(thermal_total),
            renewable_mw_by_group=_rounded(renewable_total),
            storage_by_group={
                group: StorageCapacity(injection_mw=round(i, 1), withdrawal_mw=round(w, 1), reservoir_mwh=round(r, 1))
                for group, (i, w, r) in storage_total.items()
            },
            disabled_objects=dict(disabled),
            enabled_without_capacity=dict(empty),
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_table(
        study_id: StudyId,
        kind: Annotated[TableKind, Field(description="Kind of objects.")],
        columns: Annotated[
            list[str] | None,
            Field(description="Properties to return (camelCase, e.g. ['unitCount', 'nominalCapacity']); default all."),
        ] = None,
        area_id: Annotated[AreaId | None, Field(description="Only the objects of this area.")] = None,
        only_enabled: Annotated[bool, Field(description="Skip disabled objects.")] = False,
        max_rows: Annotated[int, Field(ge=1, le=2000)] = 300,
    ) -> TableResult:
        """
        Get the properties of all the objects of a kind in one call (the "table mode" of Antares Web):
        e.g. every thermal cluster with its capacity, costs and constraints. Rows are identified by
        `area`, `area1 / area2` (links) or `area / cluster`.
        """
        requested = list(columns) if columns else None
        if requested and only_enabled and "enabled" not in requested:
            requested.append("enabled")
        table = await guard(client.get_table(study_id, kind, requested))
        rows = [
            {"id": row_id, **values}
            for row_id, values in table.items()
            if (area_id is None or area_id in row_area_ids(kind, row_id))
            and not (only_enabled and values.get("enabled") is False)
        ]
        names = sorted({name for row in rows for name in row if name != "id"})
        return TableResult(
            kind=kind,
            columns=["id", *names],
            rows=rows[:max_rows],
            total_rows=len(rows),
            truncated=len(rows) > max_rows,
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_matrix_stats(
        study_id: StudyId,
        path: Annotated[
            str | None,
            Field(
                description=(
                    "Path of the matrix in the study, e.g. 'input/load/series/load_fr', "
                    "'input/thermal/series/<area>/<cluster id>/series' (availability, MW), "
                    "'input/renewables/series/<area>/<cluster id>/series', "
                    "'input/links/<area1>/capacities/<area2>_direct' (or _indirect, area1 < area2), "
                    "'input/bindingconstraints/<id>_lt' (or _gt, _eq: right-hand side), "
                    "'input/hydro/series/<area>/mod' (daily inflows, MWh), '.../ror' (run of river, MW), "
                    "'.../maxHourlyGenPower' (MW, v9.2+), 'input/misc-gen/miscgen-<area>'."
                )
            ),
        ] = None,
        matrix_id: Annotated[
            str | None, Field(description="Instead of a path: id of a matrix referenced by a variant command.")
        ] = None,
    ) -> MatrixStats:
        """
        Get statistics on a matrix (time series) of a study without downloading it in the conversation:
        size, min / mean / max, whether it is empty or constant, whether its series differ, and the sum
        of each column (the annual energy for an hourly series in MW).
        """
        if (path is None) == (matrix_id is None):
            raise ToolError("Give either `path` or `matrix_id`.")
        if matrix_id is not None:
            data = await guard(client.get_matrix_by_id(matrix_id))
        else:
            assert path is not None
            data = await guard(client.get_matrix(study_id, path))
        return matrix_stats(data)

    @mcp.tool(annotations=READ_ONLY)
    async def list_binding_constraints(
        study_id: StudyId,
        name_contains: Annotated[str | None, Field(description="Case-insensitive filter on the name.")] = None,
        max_constraints: Annotated[int, Field(ge=1, le=2000)] = 300,
    ) -> BindingConstraints:
        """
        List the binding constraints of a study with their terms written as equations
        (e.g. '0.744 x flow(fr -> z_p2g_fr)'), their time step, operator, group and the paths of their
        right-hand side matrices. Binding constraints often encode the core of a study: modulation
        limits, conversion efficiencies, energy budgets, flow-based domains...
        """
        constraints = await guard(client.list_binding_constraints(study_id))
        if name_contains:
            constraints = [bc for bc in constraints if name_contains.lower() in bc["name"].lower()]
        return BindingConstraints(
            total=len(constraints),
            returned=min(len(constraints), max_constraints),
            constraints=[
                BindingConstraintSummary(
                    id=bc["id"],
                    name=bc["name"],
                    enabled=bc.get("enabled", True),
                    time_step=bc.get("timeStep", ""),
                    operator=bc.get("operator", ""),
                    group=bc.get("group"),
                    comments=bc.get("comments") or "",
                    terms=[term_label(term) for term in bc.get("terms") or []],
                    rhs_matrices=rhs_paths(bc["id"], bc.get("operator", "")),
                )
                for bc in constraints[:max_constraints]
            ],
        )

    @mcp.tool(annotations=READ_ONLY)
    async def read_study_file(
        study_id: StudyId,
        path: Annotated[str, Field(description="Path of a text file, e.g. 'logs/log_generation_study.txt'.")],
        pattern: Annotated[
            str | None, Field(description="Only the lines matching this case-insensitive regular expression.")
        ] = None,
        distinct: Annotated[bool, Field(description="Drop repeated lines (useful for long generation logs).")] = False,
        max_lines: Annotated[int, Field(ge=1, le=2000)] = 200,
    ) -> FileExcerpt:
        """
        Read a text file of a study: generation logs and notes of the `user/` folder listed by
        `get_study_context`, or any INI file (e.g. 'settings/generaldata.ini'). Long files are filtered
        with `pattern` and `distinct`.
        """
        try:
            regex = re.compile(pattern, re.IGNORECASE) if pattern else None
        except re.error as e:
            raise ToolError(f"Invalid pattern: {e}") from e
        text = await guard(client.get_raw_text(study_id, path))
        all_lines = text.splitlines()
        lines = [line.rstrip() for line in all_lines if regex is None or regex.search(line)]
        if distinct:
            lines = list(dict.fromkeys(lines))
        return FileExcerpt(
            path=path,
            total_lines=len(all_lines),
            matching_lines=len(lines),
            lines=lines[:max_lines],
            truncated=len(lines) > max_lines,
        )
