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
Functions to iterate over output files.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, MutableSequence, Sequence

from antarest.core.exceptions import OutputSubFolderNotFound
from antarest.output.filestudy.matrixfiles import get_start_column, parse_output_file
from antarest.output.filestudy.model import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    OutputDataFrame,
    QueryFileType,
    VariableDescription,
    find_mode_dir,
)
from antarest.study.model import MatrixFrequency

logger = logging.getLogger(__name__)


def _filtered_files_listing(
    folders_to_check: list[Path],
    query_file: str,
    frequency: str,
) -> dict[str, MutableSequence[str]]:
    filtered_files: dict[str, MutableSequence[str]] = {}
    for folder_path in folders_to_check:
        for file in folder_path.iterdir():
            if file.stem == f"{query_file}-{frequency}":
                filtered_files.setdefault(folder_path.name, []).append(file.name)
    return filtered_files


@dataclass(frozen=True, order=True)
class OutputFileMetadata:
    """
    Attributes of one output matrix file.
    Uniquely identifies a file in the output.
    """

    year: int | Literal["mc-all"]
    file_type: QueryFileType
    frequency: MatrixFrequency
    element_id: str


@dataclass(frozen=True, order=True)
class OutputFile:
    metadata: OutputFileMetadata
    path: Path

    def parse(self) -> "OutputFileData":
        data = parse_output_file(self.path, get_start_column(self.metadata.frequency))
        return OutputFileData(file=self, data=data)


@dataclass(frozen=True)
class OutputFileData:
    """
    Carries information about the current state of a matrix which was read from an output file.
    """

    file: OutputFile
    data: OutputDataFrame[VariableDescription]


def _filter_files(folder_path: Path, ids: set[str]) -> list[str]:
    """
    Filters out subdirs corresponding to not-selected system elements (areas/links).
    """
    filtered = sorted([d.name for d in folder_path.iterdir()])
    if not ids:
        return filtered
    return [i for i in filtered if i in ids]


def select_mc_ind_files(
    output_path: Path,
    query_file: MCIndAreasQueryFile | MCIndLinksQueryFile,
    frequency: MatrixFrequency,
    element_ids: Sequence[str],
    mc_years: Sequence[int] | None,
) -> list[OutputFile]:
    mode_dir = find_mode_dir(output_path)
    mc_ind_path = mode_dir / MCRoot.MC_IND.value
    if not mc_ind_path.is_dir():
        raise OutputSubFolderNotFound(output_path.name, f"{mode_dir.name}/mc-ind")

    output_type = "areas" if isinstance(query_file, MCIndAreasQueryFile) else "links"

    # Monte Carlo years filtering
    all_mc_years = [d.name for d in mc_ind_path.iterdir()]
    if mc_years:
        all_mc_years = [y for y in all_mc_years if int(y) in frozenset(mc_years)]
    if not all_mc_years:
        return []

    # Links / Areas ids filtering

    # The list of areas and links is the same whatever the MC year under consideration:
    # Therefore we choose the first year by default avoiding useless scanning directory operations.
    first_mc_year = all_mc_years[0]
    areas_or_links_ids = _filter_files(mc_ind_path / first_mc_year / output_type, set(element_ids))

    # Frequency and query file filtering
    folders_to_check = [mc_ind_path / first_mc_year / output_type / id for id in areas_or_links_ids]
    filtered_files = _filtered_files_listing(folders_to_check, query_file, frequency)

    # Loop on MC years to return the whole list of files
    return [
        OutputFile(
            metadata=OutputFileMetadata(
                year=int(mc_year), file_type=query_file, frequency=frequency, element_id=element_id
            ),
            path=mc_ind_path / mc_year / output_type / element_id / file,
        )
        for mc_year in all_mc_years
        for element_id, files in filtered_files.items()
        for file in files
    ]


def select_mc_all_files(
    output_path: Path,
    query_file: MCAllAreasQueryFile | MCAllLinksQueryFile,
    frequency: MatrixFrequency,
    element_ids: Sequence[str],
) -> list[OutputFile]:
    mode_dir = find_mode_dir(output_path)
    mc_all_path = mode_dir / MCRoot.MC_ALL.value
    if not mc_all_path.exists():
        raise OutputSubFolderNotFound(output_path.name, f"{mode_dir.name}/mc-all")

    output_type = "areas" if isinstance(query_file, MCAllAreasQueryFile) else "links"

    # Links / Areas ids filtering
    areas_or_links_ids = _filter_files(mc_all_path / output_type, set(element_ids))

    # Frequency and query file filtering
    folders_to_check = [mc_all_path / output_type / id for id in areas_or_links_ids]
    filtered_files = _filtered_files_listing(folders_to_check, query_file, frequency)

    # Loop to return the whole list of files
    return [
        OutputFile(
            metadata=OutputFileMetadata(
                year="mc-all", file_type=query_file, frequency=frequency, element_id=element_id
            ),
            path=mc_all_path / output_type / element_id / file,
        )
        for element_id, files in filtered_files.items()
        for file in files
    ]


def select_files(
    output_path: Path,
    file_type: QueryFileType,
    frequency: MatrixFrequency,
    element_ids: Sequence[str],
    mc_years: Sequence[int] | None = None,
) -> list[OutputFile]:
    """
    Returns the list of matrix files that correspond to the filters in arguments.

    Notes:
        whatever the requested years, the implementation will scan years directories
        to identify what years are actually present in the output.
        If called repeatedly, it will perform poorly.
    """
    match file_type:
        case MCIndAreasQueryFile() | MCIndLinksQueryFile():
            return select_mc_ind_files(output_path, file_type, frequency, element_ids, mc_years)
        case MCAllAreasQueryFile() | MCAllLinksQueryFile():
            return select_mc_all_files(output_path, file_type, frequency, element_ids)
        case _:
            raise ValueError(f"Unknown output file type: {file_type}")


def iterate_output_data(
    output_path: Path,
    file_type: QueryFileType,
    frequency: MatrixFrequency,
    element_ids: Sequence[str],
    mc_years: Sequence[int] | None = None,
) -> Iterable[OutputFileData]:
    """
    Iterable over data as represented in antares-simulator output files.
    In particular, no transformation is performed on the shape of the output table.
    """
    output_files = select_files(output_path, file_type, frequency, element_ids, mc_years=mc_years)

    return map(OutputFile.parse, output_files)
