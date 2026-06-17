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
import io
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from antarest.core.model import JSON
from antarest.core.serde.ini_common import DUPLICATE_KEYS
from antarest.core.serde.ini_reader import IniReader
from antarest.core.utils.archives import read_original_file_in_archive
from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.output.filestudy.utils import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    QueryFileType,
    get_output_object_type,
    get_start_column,
    normalize_df_column_names,
    parse_headers,
)
from antarest.output.model import OutputVariablesList
from antarest.output.storage.output_storage import OutputDetails, OutputStorageType
from antarest.study.business.model.config.general_model import Mode
from antarest.study.model import MatrixFrequency


def parse_output_config(output_path: Path) -> JSON:
    if output_path.suffix == ".zip":
        # We need to read data from the archive
        content = read_original_file_in_archive(output_path, "about-the-study/parameters.ini")
        return IniReader(DUPLICATE_KEYS).read(io.StringIO(content.decode("utf-8")))
    return IniReader(DUPLICATE_KEYS).read(output_path / "about-the-study" / "parameters.ini")


def extract_output_details(output_path: Path) -> OutputDetails:
    # TODO: add some basic checks
    parameters_path = output_path / "about-the-study" / "parameters.ini"
    ini_reader = IniReader(special_keys=DUPLICATE_KEYS)
    parameters_dict = ini_reader.read(parameters_path)
    general = parameters_dict["general"]
    output = parameters_dict["output"]
    mode = Mode(general["mode"])
    return OutputDetails(
        name=output_path.name,  # TODO: should it be re-built from data instead ?
        mode=mode,
        synthesis=output["synthesis"],
        by_year=general["year-by-year"],
        nb_years=general["nbyears"],
        archived=False,
        storage_type=OutputStorageType.IN_STUDY_FILE_TREE,
    )


def find_simulation_log(output_dir: Path, log_type: LogType) -> Path | None:
    log_locations = {
        LogType.STDOUT: [
            output_dir / "antares-out.log",
            output_dir / "simulation.log",
        ],
        LogType.STDERR: [
            output_dir / "antares-err.log",
        ],
    }
    return next((loc for loc in log_locations[log_type] if loc.is_file()), None)


def find_logs(output_dir: Path) -> SimulationLogs:
    return SimulationLogs(
        out=find_simulation_log(output_dir, LogType.STDOUT), err=find_simulation_log(output_dir, LogType.STDERR)
    )


@dataclass(frozen=True)
class ColumnHeader:
    name: str
    sub_columns_names: list[str] = field(default_factory=list)


def _filter_files_with_same_prefix(
    parent_folder: Path, file_type_class: type[QueryFileType]
) -> dict[QueryFileType, MatrixFrequency]:
    """
    Iterate over all existing files inside the parent_folder.
    Returns only one file for each query file class.
    This way we avoid opening files we know will have the same headers

    Example:
        In the folder, there's 4 files:
        `values-hourly.txt`, `values-weekly.txt`, `values-monthly.txt` and `details-annual.txt`
        The method will only return 1 `values` file and the `details` one.

    Args:
        - parent_folder: parent folder containing several files
        - file_type_class: query file type class.

    Returns:
        - A mapping from file type class to a certain existing matrix frequency
    """
    all_files = [d.name for d in parent_folder.iterdir()]
    file_dict = {}
    for file in all_files:
        splitted_file_name = file.removesuffix(".txt").split("-")
        if len(splitted_file_name) == 2:
            file_type, freq = splitted_file_name
        else:
            file_type1, file_type2, freq = splitted_file_name
            file_type = f"{file_type1}-{file_type2}"
        file_dict[file_type_class(file_type)] = MatrixFrequency(freq)
    return file_dict


def _read_headers_only(
    file_path: Path, mc_root: MCRoot, file_type: QueryFileType, start_column: int
) -> list[ColumnHeader]:
    """
    Returns the headers of a given output file.

    Args:
        - file_path: path of the output file
        - mc_root: mc-ind or mc-all
        - freq: MatrixFrequency of the given file.
        - file_type: query file type class.

    Returns:
        - A list of ColumnHeader objects
    """
    output_headers = parse_headers(file_path.read_text(encoding="utf-8"), start_column)

    if "details" in file_type.value:
        cols_mapping: dict[str, set[str]] = {}
        for col in output_headers:
            cols_mapping.setdefault(col[0], set()).add(col[1])
        return [ColumnHeader(name=col, sub_columns_names=list(vars)) for col, vars in cols_mapping.items()]

    return [ColumnHeader(name=col) for col in normalize_df_column_names(mc_root, output_headers)]


def _get_all_headers_and_file_type(
    mc_root: MCRoot, parent_path: Path, file_type_class: type[QueryFileType]
) -> Iterator[tuple[list[ColumnHeader], QueryFileType]]:
    """
    Returns the headers of all output files located in the parent_path.
    For each header, also returns it corresponding file type.
    """
    filtered_files = _filter_files_with_same_prefix(parent_path, file_type_class)
    for file_type, freq in filtered_files.items():
        file_path = parent_path / f"{file_type}-{freq.value}.txt"
        start_col = get_start_column(freq)
        yield _read_headers_only(file_path, mc_root, file_type, start_col), file_type


def extract_variables_list(output_path: Path) -> OutputVariablesList:
    """
    For a given output path, iterates over all necessary files to gather the possible variables it contains.
    It classifies them under categories inside a Pydantic model.
    This operation can take dozens of seconds as there are potentially hundreds of files to parse.
    """

    # Build paths to parse data from
    existing_paths: list[Path] = []

    for mode in {"economy", "adequacy"}:
        mc_ind_path = output_path / mode / MCRoot.MC_IND.value
        if mc_ind_path.exists():
            first_mc_year = sorted(mc_ind_path.iterdir())[0].name
            existing_paths.append(mc_ind_path / first_mc_year)
        mc_all_path = output_path / mode / MCRoot.MC_ALL.value
        if mc_all_path.exists():
            existing_paths.append(mc_all_path)

    variables: dict[str, Any] = {"mc_ind": {"areas": [], "links": []}, "mc_all": {"areas": [], "links": []}}

    # Iterate over paths and gather data
    for mc_path in existing_paths:
        mc_root = MCRoot.MC_ALL if mc_path.name == MCRoot.MC_ALL.value else MCRoot.MC_IND
        mc_root_key = "mc_all" if mc_root == MCRoot.MC_ALL else "mc_ind"

        # Areas
        areas_folder = mc_path / "areas"
        file_type_class = MCIndAreasQueryFile if mc_root == MCRoot.MC_IND else MCAllAreasQueryFile
        if areas_folder.exists():
            for area in sorted(areas_folder.iterdir()):
                areas_dict: dict[str, Any] = {"name": area.name}
                parent_path = areas_folder / area.name

                for col_headers, file_type in _get_all_headers_and_file_type(mc_root, parent_path, file_type_class):
                    object_type = get_output_object_type(file_type, is_link=False)
                    key = "variables" if object_type == "areas" else object_type
                    if "details" in file_type.value:
                        areas_dict[key] = [{"name": c.name, "variables": c.sub_columns_names} for c in col_headers]
                    else:
                        areas_dict[key] = areas_dict.get(key, set()) | {col.name for col in col_headers}

                variables[mc_root_key]["areas"].append(areas_dict)

        # Links
        links_folder = mc_path / "links"
        file_type_klass = MCIndLinksQueryFile if mc_root == MCRoot.MC_IND else MCAllLinksQueryFile
        if links_folder.exists():
            for link_path in sorted(links_folder.iterdir()):
                area1, area2 = link_path.name.split(" - ")
                links_dict: dict[str, Any] = {"area_1_name": area1, "area_2_name": area2}

                for col_headers, _ in _get_all_headers_and_file_type(mc_root, link_path, file_type_klass):
                    links_dict["variables"] = links_dict.get("variables", set()) | {col.name for col in col_headers}

                variables[mc_root_key]["links"].append(links_dict)

    return OutputVariablesList.model_validate(variables)
