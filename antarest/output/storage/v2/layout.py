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
"""Shared source-file layout for metadata discovery, writing and reading."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from antarest.output.filestudy.model import FileOutput, VariableDescription
from antarest.output.storage.v2.dbmodel import ElementType, ScenarioAggregation
from antarest.study.model import MatrixFrequency

CLUSTER_TYPES: tuple[ElementType, ...] = ("thermal_cluster", "renewable_cluster", "short_term_storage")
FILE_TYPES: dict[str, ElementType] = {
    "values": "area",
    "details": "thermal_cluster",
    "details-res": "renewable_cluster",
    "details-STstorage": "short_term_storage",
    "id": "area_id",
}
OBJECT_NAMES: dict[ElementType, str] = {
    "area": "areas",
    "link": "links",
    "thermal_cluster": "thermal_clusters",
    "renewable_cluster": "renewable_clusters",
    "short_term_storage": "short_term_storages",
    "binding_constraint": "binding_constraints",
    "area_id": "areas_id",
    "link_id": "links_id",
}


@dataclass(frozen=True)
class SourceFile:
    path: Path
    aggregation: ScenarioAggregation
    element_type: ElementType
    frequency: MatrixFrequency
    year: int
    element_id: str


def source_files(output: FileOutput) -> Iterator[SourceFile]:
    roots: list[tuple[ScenarioAggregation, int, Path]] = [("mc-all", 0, output.mc_all_dir)]
    roots.extend(("mc-ind", year, output.get_mc_year_dir(year)) for year in output.mc_years)
    for aggregation, year, root in roots:
        for folder in ("areas", "links", "binding_constraints"):
            parent = root / folder
            if not parent.is_dir():
                continue
            paths = parent.glob("*.txt") if folder == "binding_constraints" else parent.glob("*/*.txt")
            for path in sorted(paths):
                prefix, _, freq = path.stem.rpartition("-")
                try:
                    frequency = MatrixFrequency(freq)
                except ValueError:
                    continue
                if folder == "binding_constraints":
                    element_type: ElementType = "binding_constraint"
                    element_id = prefix
                else:
                    if prefix not in FILE_TYPES:
                        continue
                    element_type = FILE_TYPES[prefix]
                    if folder == "links":
                        if prefix not in ("values", "id"):
                            continue
                        element_type = "link" if prefix == "values" else "link_id"
                    element_id = path.parent.name
                yield SourceFile(path, aggregation, element_type, frequency, year, element_id)


@dataclass(frozen=True)
class HeaderGroup:
    cluster_id: str | None
    positions: list[int]
    variables: list[VariableDescription]


def header_groups(headers: Sequence[VariableDescription], element_type: ElementType) -> list[HeaderGroup]:
    """Move the cluster name into a row key, identically for discovery and writing.

    Details headers use the first line for the cluster ID and the second for the
    metric (e.g. NP Cost - Euro). Retain that line verbatim as unit for download.
    """
    if element_type not in CLUSTER_TYPES:
        return [HeaderGroup(None, list(range(len(headers))), list(headers))]
    groups: dict[str, HeaderGroup] = {}
    for position, header in enumerate(headers):
        group = groups.setdefault(header.name, HeaderGroup(header.name, [], []))
        group.positions.append(position)
        group.variables.append(VariableDescription(header.unit_repr(), header.unit, header.statistic_type))
    return list(groups.values())


def index_columns(aggregation: ScenarioAggregation, element_type: ElementType) -> list[str]:
    ids = ["link"] if element_type in ("link", "link_id") else ["area"]
    if element_type == "binding_constraint":
        ids = ["constraint"]
    if element_type in CLUSTER_TYPES:
        ids.append("cluster")
    return (["mcYear"] if aggregation == "mc-ind" else []) + ids + ["timeId"]


def parquet_filename(aggregation: ScenarioAggregation, element_type: ElementType, frequency: MatrixFrequency) -> str:
    return f"{aggregation}_{OBJECT_NAMES[element_type]}_{frequency.value}.parquet"
