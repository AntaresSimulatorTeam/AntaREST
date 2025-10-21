# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from antarest.study.business.output.utils import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    QueryFileType,
    normalize_column_names,
    parse_output_file,
)
from antarest.study.storage.output_model import OutputVariablesMetadata
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


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
    file_path: Path, mc_root: MCRoot, freq: MatrixFrequency, file_type: QueryFileType
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
    body = parse_output_file(file_path, freq, 0)

    if "details" in file_type.value:
        cols_mapping: dict[str, set[str]] = {}
        for col in body.columns:
            cols_mapping.setdefault(col[0], set()).add(col[1])
        return [ColumnHeader(name=col, sub_columns_names=list(vars)) for col, vars in cols_mapping.items()]

    normalized_cols = normalize_column_names(body, mc_root)
    return [ColumnHeader(name=col) for col in normalized_cols]


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
        yield _read_headers_only(file_path, mc_root, freq, file_type), file_type


def extract_variables_metadata(output_path: Path) -> OutputVariablesMetadata:
    """
    For a given output path, iterates over all necessary files to gather the possible variables it contains.
    It classifies them under categories inside a Pydantic model.
    This operation can take dozens of seconds as there are potentially hundreds of files to parse.
    """
    # Initialization
    mc_ind_path = output_path / "economy" / MCRoot.MC_IND.value
    mc_all_path = output_path / "economy" / MCRoot.MC_ALL.value

    variables: dict[str, Any] = {"mc_ind": {"areas": [], "links": []}, "mc_all": {"areas": [], "links": []}}

    areas_mapping = {
        "details": "thermal_clusters",
        "details-res": "renewable_clusters",
        "details-STstorage": "short_term_storages",
        "values": "variables",
        "id": "variables",
    }

    existing_paths = []
    if mc_ind_path.exists():
        first_mc_year = sorted(mc_ind_path.iterdir())[0].name
        existing_paths.append(mc_ind_path / first_mc_year)
    if mc_all_path.exists():
        existing_paths.append(mc_all_path)

    for mc_path in existing_paths:
        mc_root = MCRoot.MC_ALL if mc_path == mc_all_path else MCRoot.MC_IND
        mc_root_key = "mc_all" if mc_root == MCRoot.MC_ALL else "mc_ind"

        # Areas
        areas_folder = mc_path / "areas"
        file_type_class = MCIndAreasQueryFile if mc_root == MCRoot.MC_IND else MCAllAreasQueryFile
        if areas_folder.exists():
            for area in sorted(areas_folder.iterdir()):
                areas_dict: dict[str, Any] = {"name": area.name}
                parent_path = areas_folder / area

                for col_headers, file_type in _get_all_headers_and_file_type(mc_root, parent_path, file_type_class):
                    key = areas_mapping[file_type.value]
                    if "details" in file_type.value:
                        areas_dict[key] = [{"name": c.name, "variables": c.sub_columns_names} for c in col_headers]
                    else:
                        areas_dict[key] = areas_dict.get(key, set()) | {col.name for col in col_headers}

                variables[mc_root_key]["areas"].append(areas_dict)

        # Links
        links_folder = mc_path / "links"
        file_type_klass = MCIndLinksQueryFile if mc_root == MCRoot.MC_IND else MCAllLinksQueryFile
        if links_folder.exists():
            for link_name in sorted(links_folder.iterdir()):
                area1, area2 = link_name.name.split("-")
                links_dict: dict[str, Any] = {"area_1_name": area1, "area_2_name": area2}
                parent_path = links_folder / link_name

                for col_headers, _ in _get_all_headers_and_file_type(mc_root, parent_path, file_type_klass):
                    links_dict["variables"] = links_dict.get("variables", set()) | {col.name for col in col_headers}

                variables[mc_root_key]["links"].append(links_dict)

    return OutputVariablesMetadata.model_validate(variables)
