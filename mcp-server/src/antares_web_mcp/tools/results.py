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
Tools to read simulation results.

Antares Web aggregates the Monte-Carlo synthesis of an output into a CSV file with more than
a hundred columns. These tools download it and return only the requested indicators, as a
compact table, to keep the answer readable for the model.
"""

import csv
import io
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.tools.common import READ_ONLY, OutputId, StudyId, guard

Frequency = Literal["annual", "monthly", "weekly", "daily", "hourly"]
Statistic = Literal["EXP", "STD", "MIN", "MAX"]
STATISTICS = {"EXP", "STD", "MIN", "MAX", "VALUES"}

AREA_KEY_INDICATORS = [
    "OV. COST",
    "OP. COST",
    "MRG. PRICE",
    "LOAD",
    "BALANCE",
    "UNSP. ENRG",
    "SPIL. ENRG",
    "LOLD",
    "CO2 EMIS.",
]
# Production columns, by thermal group / renewable group / hydro: returned by default when not empty.
AREA_PRODUCTION_INDICATORS = {
    "NUCLEAR",
    "LIGNITE",
    "COAL",
    "GAS",
    "OIL",
    "MIX. FUEL",
    "MISC. DTG",
    "MISC. DTG 2",
    "MISC. DTG 3",
    "MISC. DTG 4",
    "WIND OFFSHORE",
    "WIND ONSHORE",
    "SOLAR CONCRT.",
    "SOLAR PV",
    "SOLAR ROOFT",
    "RENW. 1",
    "RENW. 2",
    "RENW. 3",
    "RENW. 4",
    "H. ROR",
    "H. STOR",
}
LINK_KEY_INDICATORS = [
    "FLOW LIN.",
    "UCAP LIN.",
    "CONG. FEE (ALG.)",
    "MARG. COST",
    "CONG. PROB +",
    "CONG. PROB -",
    "HURDLE COST",
]
# Columns of the short-term storage details file (one row per storage), without statistic suffix.
STORAGE_INDICATORS = ["P-injection - MW", "P-withdrawal - MW", "Levels - MWh", "CashFlow - Euro"]

INDICATORS_HELP = (
    "Indicator names as in Antares outputs, e.g. 'OV. COST' (overall cost, EUR), 'MRG. PRICE' (marginal price, "
    "EUR/MWh), 'LOAD', 'UNSP. ENRG' (unsupplied energy, MWh), 'SPIL. ENRG', 'LOLD' (loss of load duration, h), "
    "'CO2 EMIS.', a production group such as 'NUCLEAR', 'GAS', 'WIND ONSHORE', 'SOLAR PV', or a short-term "
    "storage group such as 'BATTERY_INJECTION', 'BATTERY_WITHDRAWAL', 'BATTERY_LEVEL', 'PSP_OPEN_INJECTION' "
    "(for each storage, use `get_storage_results`). Unknown names are ignored and reported in "
    "`ignored_indicators`. Default: the key indicators."
)


class OutputSummary(BaseModel):
    id: str
    mode: str | None = None
    nb_years: int | None = None
    synthesis: bool | None = Field(default=None, description="Whether Monte-Carlo synthesis results are available.")
    year_by_year: bool | None = None
    archived: bool | None = None


class ResultsTable(BaseModel):
    frequency: str
    statistic: str = Field(description="Statistic over the Monte-Carlo years (EXP = expectation / mean).")
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    truncated: bool = Field(description="True if only the first `max_rows` rows are returned.")
    ignored_indicators: list[str] | None = Field(
        default=None, description="Requested indicators that do not exist in this output: they were ignored."
    )
    available_indicators: list[str] | None = Field(
        default=None, description="All the indicators of this output, given when some requested ones were ignored."
    )


def register(mcp: MCPServer, client: AntaresWebClient, *, read_only: bool) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def list_outputs(study_id: StudyId) -> list[OutputSummary]:
        """List the simulation outputs (results) of a study."""
        outputs = await guard(client.list_outputs(study_id))
        return [
            OutputSummary(
                id=output["id"],
                mode=output.get("mode"),
                nb_years=output.get("nbYears"),
                synthesis=output.get("synthesis"),
                year_by_year=output.get("byYear"),
                archived=output.get("archived"),
            )
            for output in outputs
        ]

    @mcp.tool(annotations=READ_ONLY)
    async def get_area_results(
        study_id: StudyId,
        output_id: OutputId,
        frequency: Annotated[Frequency, Field(description="Time resolution of the results.")] = "annual",
        areas: Annotated[list[str] | None, Field(description="Area ids to keep. Default: all areas.")] = None,
        indicators: Annotated[list[str] | None, Field(description=INDICATORS_HELP)] = None,
        statistic: Annotated[Statistic, Field(description="Statistic over the Monte-Carlo years.")] = "EXP",
        max_rows: Annotated[int, Field(ge=1, le=2000, description="Maximum number of rows returned.")] = 100,
    ) -> ResultsTable:
        """
        Get the results of a simulation for areas (Monte-Carlo synthesis): costs, marginal prices,
        unsupplied energy, production by group, ... One row per area and time step.
        """
        content = await guard(
            client.aggregate_output(
                study_id, output_id, target="areas", query_file="values", frequency=frequency, ids=areas
            )
        )
        return build_results_table(
            content,
            id_columns=["area"],
            frequency=frequency,
            statistic=statistic,
            indicators=indicators,
            default_indicators=AREA_KEY_INDICATORS,
            optional_indicators=AREA_PRODUCTION_INDICATORS,
            keep_ids=areas,
            max_rows=max_rows,
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_link_results(
        study_id: StudyId,
        output_id: OutputId,
        frequency: Annotated[Frequency, Field(description="Time resolution of the results.")] = "annual",
        links: Annotated[
            list[str] | None, Field(description="Links to keep, as 'area1 - area2' (alphabetical order).")
        ] = None,
        indicators: Annotated[
            list[str] | None,
            Field(
                description=(
                    "Indicator names, e.g. 'FLOW LIN.' (flow, MWh), 'UCAP LIN.', 'CONG. FEE (ALG.)', "
                    "'MARG. COST', 'CONG. PROB +'. Default: the key indicators."
                )
            ),
        ] = None,
        statistic: Annotated[Statistic, Field(description="Statistic over the Monte-Carlo years.")] = "EXP",
        max_rows: Annotated[int, Field(ge=1, le=2000, description="Maximum number of rows returned.")] = 100,
    ) -> ResultsTable:
        """
        Get the results of a simulation for links (Monte-Carlo synthesis): flows, congestion fees and
        probabilities, ... One row per link and time step. A positive flow goes from area1 to area2.
        """
        content = await guard(
            client.aggregate_output(study_id, output_id, target="links", query_file="values", frequency=frequency)
        )
        return build_results_table(
            content,
            id_columns=["link"],
            frequency=frequency,
            statistic=statistic,
            indicators=indicators,
            default_indicators=LINK_KEY_INDICATORS,
            optional_indicators=set(),
            keep_ids=links,
            max_rows=max_rows,
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_storage_results(
        study_id: StudyId,
        output_id: OutputId,
        frequency: Annotated[Frequency, Field(description="Time resolution of the results.")] = "annual",
        areas: Annotated[list[str] | None, Field(description="Area ids to keep. Default: all areas.")] = None,
        max_rows: Annotated[int, Field(ge=1, le=2000, description="Maximum number of rows returned.")] = 100,
    ) -> ResultsTable:
        """
        Get the results of each short-term storage (battery, pumped storage...) of a simulation
        (Monte-Carlo expectation): charging power 'P-injection - MW', discharging power
        'P-withdrawal - MW', stored energy 'Levels - MWh' and 'CashFlow - Euro'. One row per storage
        ('cluster' column) and time step. Use an hourly or daily frequency to see when storages charge
        and discharge: this is how to check whether a storage was actually used.
        """
        content = await guard(
            client.aggregate_output(
                study_id, output_id, target="areas", query_file="details-STstorage", frequency=frequency, ids=areas
            )
        )
        return build_results_table(
            content,
            id_columns=["area", "cluster"],
            frequency=frequency,
            statistic="EXP",
            indicators=None,
            default_indicators=STORAGE_INDICATORS,
            optional_indicators=set(),
            keep_ids=areas,
            max_rows=max_rows,
        )


def _normalize(name: str) -> str:
    return " ".join(name.upper().replace(".", " ").split())


def _split_column(column: str) -> tuple[str, str]:
    """Splits 'MRG. PRICE EXP' into ('MRG. PRICE', 'EXP')."""
    base, _, stat = column.rpartition(" ")
    return (base, stat) if stat in STATISTICS and base else (column, "")


def _to_number(value: str) -> float | str | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return value


def _to_time(value: str) -> int | str:
    """Time step index (1-based: year, month, week, day or hour number)."""
    try:
        return int(float(value))
    except ValueError:
        return value


def build_results_table(
    content: str,
    *,
    id_columns: list[str],
    frequency: str,
    statistic: str,
    indicators: list[str] | None,
    default_indicators: list[str],
    optional_indicators: set[str],
    keep_ids: list[str] | None,
    max_rows: int,
) -> ResultsTable:
    """
    Filters the aggregated CSV of an output: selected rows, selected indicators, one statistic.

    Rows are identified by `id_columns` (`keep_ids` filters on the first one) and the time step.
    """
    rows = list(csv.DictReader(io.StringIO(content)))
    if not rows:
        raise ToolError("The output contains no result for this selection.")
    if keep_ids:
        wanted = {_normalize(i) for i in keep_ids}
        rows = [row for row in rows if _normalize(row.get(id_columns[0], "")) in wanted]
        if not rows:
            raise ToolError(f"No result for {keep_ids}: check the ids (see `describe_study`).")

    # Available indicators -> CSV column, for the requested statistic, or the single column of an indicator
    # without statistic ('VALUES' suffix, or no suffix at all as in the short-term storage details file).
    available: dict[str, str] = {}
    for column in rows[0]:
        if column in id_columns or column == "timeId":
            continue
        base, stat = _split_column(column)
        if stat == statistic or (stat in {"VALUES", ""} and base not in available):
            available[base] = column

    # Unknown indicators are ignored (and reported) rather than failing the whole call: the model often asks
    # for a mix of real and guessed names, and the real ones are still worth returning.
    ignored: list[str] = []
    if indicators:
        by_normalized = {_normalize(base): base for base in available}
        selected: list[str] = []
        for name in indicators:
            matches = [base for norm, base in by_normalized.items() if norm == _normalize(name)]
            matches = matches or [base for norm, base in by_normalized.items() if norm.startswith(_normalize(name))]
            if not matches:
                ignored.append(name)
            selected.extend(m for m in matches if m not in selected)
        if not selected:
            names = ", ".join(f"'{name}'" for name in ignored)
            plural = "s" if len(ignored) > 1 else ""
            raise ToolError(f"Unknown indicator{plural} {names}. Available indicators: {sorted(available)}.")
    else:
        selected = [base for base in default_indicators if base in available]
        selected += sorted(
            base
            for base in available
            if base in optional_indicators and any(_to_number(row[available[base]]) not in (None, 0.0) for row in rows)
        )

    table = [
        {column: row.get(column) for column in id_columns}
        | {"time": _to_time(row.get("timeId", ""))}
        | {base: _to_number(row[available[base]]) for base in selected}
        for row in rows
    ]
    return ResultsTable(
        frequency=frequency,
        statistic=statistic,
        columns=[*id_columns, "time", *selected],
        rows=table[:max_rows],
        total_rows=len(table),
        truncated=len(table) > max_rows,
        ignored_indicators=ignored or None,
        available_indicators=sorted(available) if ignored else None,
    )
