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
from typing import Annotated, Any, Iterator, Literal, Tuple

from pydantic import BaseModel, Field
from sqlalchemy import select
from typing_extensions import TypeAlias

from antarest.core.exceptions import OutputVariablesViewError
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.study.model import MatrixFrequency
from antarest.study.output.output_model import OutputVariablesList, OutputVariablesViewsModel
from antarest.study.output.utils import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    QueryFileType,
    get_start_column,
    normalize_df_column_names,
    parse_headers,
)


class ThermalClusterOutputId(BaseModel, extra="forbid"):
    type: Literal["thermal"] = "thermal"
    area_id: str
    thermal_id: str


class RenewableClusterOutputId(BaseModel, extra="forbid"):
    type: Literal["renewable"] = "renewable"
    area_id: str
    renewable_id: str


class ShortTermStorageOutputId(BaseModel, extra="forbid"):
    type: Literal["st_storage"] = "st_storage"
    area_id: str
    st_storage_id: str


class LinkOutputId(BaseModel, extra="forbid"):
    type: Literal["link"] = "link"
    area_from_id: str
    area_to_id: str


class AreaOutputId(BaseModel, extra="forbid"):
    type: Literal["area"] = "area"
    area_id: str


OutputItemId: TypeAlias = Annotated[
    AreaOutputId | LinkOutputId | ThermalClusterOutputId | RenewableClusterOutputId | ShortTermStorageOutputId,
    Field(discriminator="type"),
]

SubAreaItemId: TypeAlias = Annotated[
    AreaOutputId | ThermalClusterOutputId | RenewableClusterOutputId | ShortTermStorageOutputId,
    Field(discriminator="type"),
]


def get_ids_for_aggregation(item_id: OutputItemId) -> Tuple[str, str | None]:
    match item_id:
        case AreaOutputId():
            return item_id.area_id, None
        case LinkOutputId():
            return f"{item_id.area_from_id} - {item_id.area_to_id}", None
        case ThermalClusterOutputId():
            return item_id.area_id, item_id.thermal_id
        case RenewableClusterOutputId():
            return item_id.area_id, item_id.renewable_id
        case ShortTermStorageOutputId():
            return item_id.area_id, item_id.st_storage_id
        case _:
            raise NotImplementedError("Unknown output item type")


def get_query_file(item_id: OutputItemId) -> QueryFileType:
    match item_id:
        case AreaOutputId():
            return MCIndAreasQueryFile.VALUES
        case LinkOutputId():
            return MCIndLinksQueryFile.VALUES
        case ThermalClusterOutputId():
            return MCIndAreasQueryFile.DETAILS
        case RenewableClusterOutputId():
            return MCIndAreasQueryFile.DETAILS_RES
        case ShortTermStorageOutputId():
            return MCIndAreasQueryFile.DETAILS_ST_STORAGE
        case _:
            raise NotImplementedError("Unknown output item type")


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
                parent_path = areas_folder / area.name

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
            for link_path in sorted(links_folder.iterdir()):
                area1, area2 = link_path.name.split(" - ")
                links_dict: dict[str, Any] = {"area_1_name": area1, "area_2_name": area2}

                for col_headers, _ in _get_all_headers_and_file_type(mc_root, link_path, file_type_klass):
                    links_dict["variables"] = links_dict.get("variables", set()) | {col.name for col in col_headers}

                variables[mc_root_key]["links"].append(links_dict)

    return OutputVariablesList.model_validate(variables)


def check_output_variable_exists(
    output_id: str,
    variable_name: str,
    available_variables: OutputVariablesList,
    output_identifier: OutputItemId,
) -> None:
    match output_identifier:
        case LinkOutputId():
            _checks_links_variables_view_coherence(output_id, available_variables, variable_name, output_identifier)
        case _:
            _checks_areas_variables_view_coherence(output_id, available_variables, variable_name, output_identifier)


def _checks_links_variables_view_coherence(
    output_id: str,
    available_variables: OutputVariablesList,
    variable_name: str,
    output_identifier: LinkOutputId,
) -> None:
    area_from_id = output_identifier.area_from_id
    area_to_id = output_identifier.area_to_id
    error_msg = f"The variable '{variable_name}' does not exist for link '{area_from_id} - {area_to_id}'"
    link_variables = available_variables.mc_ind.links
    for link_variable in link_variables:
        if link_variable.area_1_name == area_from_id and link_variable.area_2_name == area_to_id:
            if variable_name in link_variable.variables:
                return
            raise OutputVariablesViewError(output_id, error_msg)

    raise OutputVariablesViewError(output_id, error_msg)


def _checks_areas_variables_view_coherence(
    output_id: str,
    available_variables: OutputVariablesList,
    variable_name: str,
    output_identifier: SubAreaItemId,
) -> None:
    error_msg = (
        f"The variable '{variable_name}' does not exist for area '{output_identifier.area_id}' and type "
        f"'{output_identifier.type}'"
    )
    area_variables = available_variables.mc_ind.areas
    for area_variable in area_variables:
        if area_variable.name == output_identifier.area_id:
            match output_identifier:
                case AreaOutputId():
                    if variable_name in area_variable.variables:
                        return
                    raise OutputVariablesViewError(output_id, error_msg)
                case ThermalClusterOutputId():
                    item_id = output_identifier.thermal_id
                    variables = area_variable.thermal_clusters
                case RenewableClusterOutputId():
                    item_id = output_identifier.renewable_id
                    variables = area_variable.renewable_clusters
                case ShortTermStorageOutputId():
                    item_id = output_identifier.st_storage_id
                    variables = area_variable.short_term_storages
                case _:
                    raise OutputVariablesViewError(output_id, error_msg)
            for item_vars in variables:
                if item_vars.name == item_id:
                    if variable_name in item_vars.variables:
                        return
                    raise OutputVariablesViewError(output_id, error_msg)

    raise OutputVariablesViewError(output_id, error_msg)


def get_output_view_inside_db(
    study_id: str,
    output_id: str,
    variable_name: str,
    frequency: MatrixFrequency,
    item_id: OutputItemId,
) -> OutputVariablesViewsModel | None:
    stmt = select(OutputVariablesViewsModel)
    stmt = stmt.where(OutputVariablesViewsModel.study_id == study_id)
    stmt = stmt.where(OutputVariablesViewsModel.output_id == output_id)
    stmt = stmt.where(OutputVariablesViewsModel.type == item_id.type)
    stmt = stmt.where(OutputVariablesViewsModel.frequency == frequency)
    stmt = stmt.where(OutputVariablesViewsModel.variable_name == variable_name)

    match item_id:
        case AreaOutputId():
            filters = [(OutputVariablesViewsModel.area_id, item_id.area_id)]
        case ThermalClusterOutputId():
            filters = [(OutputVariablesViewsModel.area_id, item_id.area_id)]
            filters.append((OutputVariablesViewsModel.thermal_id, item_id.thermal_id))
        case RenewableClusterOutputId():
            filters = [(OutputVariablesViewsModel.area_id, item_id.area_id)]
            filters.append((OutputVariablesViewsModel.renewable_id, item_id.renewable_id))
        case ShortTermStorageOutputId():
            filters = [(OutputVariablesViewsModel.area_id, item_id.area_id)]
            filters.append((OutputVariablesViewsModel.st_storage_id, item_id.st_storage_id))
        case LinkOutputId():
            filters = [(OutputVariablesViewsModel.area_from_id, item_id.area_from_id)]
            filters.append((OutputVariablesViewsModel.area_to_id, item_id.area_to_id))
        case _:
            raise NotImplementedError(f"output identifier `{item_id.__class__}` is not implemented")

    for column, value in filters:
        stmt = stmt.where(column == value)

    return db.session.scalar(stmt)


def create_output_view_db_model(
    study_id: str,
    output_id: str,
    variable_name: str,
    frequency: MatrixFrequency,
    output_identifier: OutputItemId,
    matrix_id: str,
) -> OutputVariablesViewsModel:
    model = OutputVariablesViewsModel(
        study_id=study_id,
        output_id=output_id,
        type=output_identifier.type,
        frequency=frequency,
        variable_name=variable_name,
        matrix_id=matrix_id,
        last_read=current_time(),
    )

    match output_identifier:
        case AreaOutputId():
            model.area_id = output_identifier.area_id
        case ThermalClusterOutputId():
            model.area_id = output_identifier.area_id
            model.thermal_id = output_identifier.thermal_id
        case RenewableClusterOutputId():
            model.area_id = output_identifier.area_id
            model.renewable_id = output_identifier.renewable_id
        case ShortTermStorageOutputId():
            model.area_id = output_identifier.area_id
            model.st_storage_id = output_identifier.st_storage_id
        case LinkOutputId():
            model.area_from_id = output_identifier.area_from_id
            model.area_to_id = output_identifier.area_to_id
        case _:
            raise NotImplementedError(f"output identifier `{output_identifier.__class__}` is not implemented")

    return model
