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
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, MutableSequence, Sequence

from antarest.core.exceptions import MCRootNotHandled, OutputSubFolderNotFound
from antarest.output.filestudy.utils import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    QueryFileType,
    get_start_column,
    parse_output_file,
)
from antarest.output.model.output_data import OutputTable
from antarest.study.model import MatrixFrequency

logger = logging.getLogger(__name__)


def _find_mode_dir(output_dir: Path) -> Path | None:
    for mode_name in ("economy", "adequacy"):
        mode_dir = output_dir / mode_name
        if mode_dir.exists():
            return mode_dir
    return None


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
class OutputFile:
    path: Path
    year: int | None
    location: str


@dataclass(frozen=True)
class OutputFileData:
    """
    Carries information about the current state of a matrix which was read from an output file, and possibly already
    transformed (column fitlers, pivots, ...).
    """

    path: Path  # File from which was read
    file_type: QueryFileType
    year: int | None  # Will be None when we're working on mc-all data
    location: str  # Area or link

    data: OutputTable


def _filter_files(folder_path: Path, ids: set[str]) -> list[str]:
    # Areas names filtering
    filtered = sorted([d.name for d in folder_path.iterdir()])
    if not ids:
        return filtered
    return [i for i in filtered if i in ids]


def identify_mc_ind_files(
    output_path: Path,
    query_file: MCIndAreasQueryFile | MCIndLinksQueryFile,
    frequency: MatrixFrequency,
    ids_to_consider: Sequence[str],
    mc_years: Sequence[int] | None,
) -> list[OutputFile]:
    mode_dir = _find_mode_dir(output_path)
    if mode_dir is None:
        raise OutputSubFolderNotFound(output_path.name, f"economy/{MCRoot.MC_IND.value}")
    mc_ind_path = mode_dir / MCRoot.MC_IND.value
    output_type = "areas" if isinstance(query_file, MCIndAreasQueryFile) else "links"

    # Monte Carlo years filtering
    if not mc_ind_path.is_dir():
        return []
    all_mc_years = [d.name for d in mc_ind_path.iterdir()]
    if mc_years:
        all_mc_years = [y for y in all_mc_years if int(y) in frozenset(mc_years)]
    if not all_mc_years:
        return []

    # Links / Areas ids filtering

    # The list of areas and links is the same whatever the MC year under consideration:
    # Therefore we choose the first year by default avoiding useless scanning directory operations.
    first_mc_year = all_mc_years[0]
    areas_or_links_ids = _filter_files(mc_ind_path / first_mc_year / output_type, set(ids_to_consider))

    # Frequency and query file filtering
    folders_to_check = [mc_ind_path / first_mc_year / output_type / id for id in areas_or_links_ids]
    filtered_files = _filtered_files_listing(folders_to_check, query_file, frequency)

    # Loop on MC years to return the whole list of files
    return [
        OutputFile(
            path=mc_ind_path / mc_year / output_type / area_or_link / file,
            year=int(mc_year),
            location=area_or_link,
        )
        for mc_year in all_mc_years
        for area_or_link, files in filtered_files.items()
        for file in files
    ]


def identify_mc_all_files(
    output_path: Path,
    query_file: MCAllAreasQueryFile | MCAllLinksQueryFile,
    frequency: MatrixFrequency,
    ids_to_consider: Sequence[str],
) -> list[OutputFile]:
    mode_dir = _find_mode_dir(output_path)
    if mode_dir is None:
        raise OutputSubFolderNotFound(output_path.name, f"economy/{MCRoot.MC_ALL.value}")
    mc_all_path = mode_dir / MCRoot.MC_ALL.value
    output_type = "areas" if isinstance(query_file, MCAllAreasQueryFile) else "links"

    # Links / Areas ids filtering
    areas_or_links_ids = _filter_files(mc_all_path / output_type, set(ids_to_consider))

    # Frequency and query file filtering
    folders_to_check = [mc_all_path / output_type / id for id in areas_or_links_ids]
    filtered_files = _filtered_files_listing(folders_to_check, query_file, frequency)

    # Loop to return the whole list of files
    return [
        OutputFile(path=mc_all_path / output_type / area_or_link / file, year=None, location=area_or_link)
        for area_or_link, files in filtered_files.items()
        for file in files
    ]


def identify_files(
    output_path: Path,
    file_type: QueryFileType,
    frequency: MatrixFrequency,
    item_ids: Sequence[str],
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
            return identify_mc_ind_files(output_path, file_type, frequency, item_ids, mc_years)
        case MCAllAreasQueryFile() | MCAllLinksQueryFile():
            return identify_mc_all_files(output_path, file_type, frequency, item_ids)
        case _:
            raise MCRootNotHandled(f"Unknown output file type: {file_type}")


def iterate_output_data(
    output_path: Path,
    file_type: QueryFileType,
    frequency: MatrixFrequency,
    location_ids: Sequence[str],
    mc_years: Sequence[int] | None = None,
) -> Iterable[OutputFileData]:
    """
    Iterable over data as represented in antares-simulator output files.
    In particular, no transformation is performed on the shape of the output table.
    """
    output_files = identify_files(output_path, file_type, frequency, location_ids, mc_years=mc_years)

    # Ignore time related columns, only get variables
    start_col = get_start_column(frequency)

    def parse_file(f: OutputFile) -> OutputFileData:
        data = parse_output_file(f.path, start_col)
        return OutputFileData(
            f.path,
            file_type=file_type,
            year=f.year,
            location=f.location,
            data=data,
        )

    return map(parse_file, output_files)
