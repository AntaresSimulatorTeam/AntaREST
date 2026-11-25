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
Survey of a study (`survey_study`): the values out of line with comparable objects.

The rules of `check_study` catch what is wrong whatever the study. This tool catches what is only
*surprising*: a plant 100 times more expensive than the others of its group, an area whose settings
differ from all its neighbours. The comparisons are computed here, with fixed thresholds, so that a
model reviewing a study comments figures it was given instead of exploring matrices by itself.

An observation is a question for the author of the study, never an error: an outlier is often a
deliberate modelling choice.
"""

import statistics
from collections import Counter, defaultdict
from typing import Any

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.tools.analysis import matrix_stats
from antares_web_mcp.tools.checks import MatrixReader, StudyData, _capacity, _enabled, load_study_data
from antares_web_mcp.tools.common import READ_ONLY, StudyId

# Objects are compared inside a group of at least this size: below, none is "the odd one".
MIN_PEERS = 4
# A value is out of line when it is this many times above (or below) the median of its peers:
# an order of magnitude, the signature of a unit or typing error, not a normal dispersion.
COST_FACTOR = 5.0
CAPACITY_FACTOR = 20.0
CAPACITY_TO_PEAK_FACTOR = 50.0
MAX_OBSERVATIONS = 30


class Observation(BaseModel):
    kind: str = Field(description="What was compared.")
    object: str = Field(description="Id of the area or cluster.")
    value: float
    reference: float = Field(description="Value of the comparable objects (median or most common value).")
    message: str


class Survey(BaseModel):
    observations: list[Observation] = Field(description="Largest gaps first. Empty: nothing is out of line.")
    compared: dict[str, int] = Field(description="Number of objects that were compared, by kind.")
    notes: list[str] = Field(description="What could not be compared.")


def _times(ratio: float) -> str:
    """'100 times' or '1/100 of', whichever reads naturally."""
    return f"{ratio:,.0f} times" if ratio >= 1 else f"1/{1 / ratio:,.0f} of"


def _group_outliers(
    thermals: dict[str, dict[str, Any]], column: str, kind: str, unit: str, factor: float
) -> list[Observation]:
    groups: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for cluster_id, row in thermals.items():
        value = float(row.get(column, 0))
        if _enabled(row) and _capacity(row) > 0 and value > 0:
            groups[str(row.get("group", ""))].append((cluster_id, value))
    observations = []
    for group, members in groups.items():
        if len(members) < MIN_PEERS:
            continue
        median = statistics.median(value for _, value in members)
        for cluster_id, value in members:
            ratio = value / median
            if ratio >= factor or ratio <= 1 / factor:
                observations.append(
                    Observation(
                        kind=kind,
                        object=cluster_id,
                        value=value,
                        reference=median,
                        message=(
                            f"{value:g} {unit}: {_times(ratio)} the median of the {len(members)} clusters of "
                            f"group '{group}' ({median:g} {unit})."
                        ),
                    )
                )
    return observations


def _unsupplied_cost_outliers(areas: dict[str, dict[str, Any]]) -> list[Observation]:
    costs = {area: float(row.get("energyCostUnsupplied", 0)) for area, row in areas.items()}
    priced = {area: cost for area, cost in costs.items() if cost > 0}  # a cost of 0 is a rule of `check_study`
    if len(priced) < MIN_PEERS:
        return []
    usual, count = Counter(priced.values()).most_common(1)[0]
    if count <= len(priced) / 2:
        return []  # no common value: nothing to differ from
    return [
        Observation(
            kind="unsupplied_energy_cost",
            object=area,
            value=cost,
            reference=usual,
            message=f"{cost:g} EUR/MWh, while {count} of {len(priced)} areas use {usual:g} EUR/MWh.",
        )
        for area, cost in priced.items()
        if cost != usual
    ]


def _capacity_to_peak_outliers(data: StudyData, peak_loads: dict[str, float]) -> list[Observation]:
    capacity: dict[str, float] = defaultdict(float)
    for table in (data.thermals, data.renewables):
        for cluster_id, row in table.items():
            if _enabled(row):
                capacity[cluster_id.split(" / ")[0]] += _capacity(row)
    observations = []
    for area, peak in peak_loads.items():
        if peak > 0 and capacity[area] / peak >= CAPACITY_TO_PEAK_FACTOR:
            observations.append(
                Observation(
                    kind="capacity_to_peak_load",
                    object=area,
                    value=capacity[area],
                    reference=peak,
                    message=(
                        f"{capacity[area]:,.0f} MW installed for a peak load of {peak:,.0f} MW: "
                        f"{capacity[area] / peak:,.0f} times its peak load."
                    ),
                )
            )
    return observations


def find_outliers(data: StudyData, peak_loads: dict[str, float]) -> Survey:
    """
    Compares the objects of a study with their peers.

    Args:
        data: The properties of the objects of the study.
        peak_loads: Peak load (MW) of the areas whose load series could be read.
    """
    observations = [
        *_group_outliers(data.thermals, "marginalCost", "thermal_marginal_cost", "EUR/MWh", COST_FACTOR),
        *_group_outliers(data.thermals, "nominalCapacity", "thermal_unit_capacity", "MW", CAPACITY_FACTOR),
        *_unsupplied_cost_outliers(data.areas),
        *_capacity_to_peak_outliers(data, peak_loads),
    ]
    # Largest gap first, whatever its direction.
    observations.sort(key=lambda o: -max(o.value / o.reference, o.reference / o.value))
    notes = []
    if len(observations) > MAX_OBSERVATIONS:
        notes.append(
            f"{len(observations)} values are out of line: only the {MAX_OBSERVATIONS} largest gaps are listed."
        )
    return Survey(
        observations=observations[:MAX_OBSERVATIONS],
        compared={
            "thermal clusters": sum(1 for row in data.thermals.values() if _enabled(row) and _capacity(row) > 0),
            "areas": len(data.areas),
            "areas with a load": sum(1 for peak in peak_loads.values() if peak > 0),
        },
        notes=notes,
    )


def register(mcp: MCPServer, client: AntaresWebClient) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def survey_study(study_id: StudyId) -> Survey:
        """
        Find the values of a study that are out of line with comparable objects: thermal clusters whose
        cost or unit capacity is an order of magnitude away from their group, areas whose unsupplied
        energy cost differs from the others, areas with far more capacity than their peak load.
        The comparisons are computed with fixed thresholds: report them as questions for the author of
        the study (an outlier is often a deliberate modelling choice), and do not recompute them.
        """
        data = await load_study_data(client, study_id)
        reader = MatrixReader(client, study_id)
        areas = sorted(data.areas)
        loads = await reader.read_all([f"input/load/series/load_{area}" for area in areas])
        peak_loads = {
            area: matrix_stats(matrix).max or 0.0
            for area, matrix in zip(areas, loads, strict=True)
            if matrix is not None
        }
        survey = find_outliers(data, peak_loads)
        if reader.failures:
            survey.notes.append(
                f"The load series of {reader.failures} areas could not be read: their capacity was not "
                "compared with their peak load."
            )
        return survey
