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
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterator

from typing_extensions import override

from antarest.core.exceptions import OutputVariablesViewError
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.study.business.output.utils import (
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
from antarest.study.model import MatrixFrequency
from antarest.study.output.output_model import OutputVariablesList, OutputVariablesType, OutputVariablesViewsModel


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


class OutputIdentifier(ABC):
    @abstractmethod
    def get_id_for_aggregation(self) -> str: ...

    @abstractmethod
    def get_sub_id_for_aggregation(self) -> str | None: ...

    @property
    @abstractmethod
    def query_file(self) -> QueryFileType: ...


@dataclass(frozen=True)
class SubAreaOutputIdentifier(OutputIdentifier, ABC):
    area_id: str

    @override
    def get_id_for_aggregation(self) -> str:
        return self.area_id


@dataclass(frozen=True)
class ClusterOutputIdentifier:
    cluster_id: str

    def get_sub_id_for_aggregation(self) -> str | None:
        return self.cluster_id


@dataclass(frozen=True)
class ThermalClusterOutputIdentifier(ClusterOutputIdentifier, SubAreaOutputIdentifier):
    query_file: Final[QueryFileType] = MCIndAreasQueryFile.DETAILS


@dataclass(frozen=True)
class RenewableClusterOutputIdentifier(ClusterOutputIdentifier, SubAreaOutputIdentifier):
    query_file: Final[QueryFileType] = MCIndAreasQueryFile.DETAILS_RES


@dataclass(frozen=True)
class ShortTermStorageOutputIdentifier(SubAreaOutputIdentifier):
    storage_id: str

    query_file: Final[QueryFileType] = MCIndAreasQueryFile.DETAILS_ST_STORAGE

    @override
    def get_sub_id_for_aggregation(self) -> str | None:
        return self.storage_id


@dataclass(frozen=True)
class LinkOutputIdentifier(OutputIdentifier):
    area_from_id: str
    area_to_id: str

    query_file: Final[QueryFileType] = MCIndLinksQueryFile.VALUES

    @override
    def get_id_for_aggregation(self) -> str:
        return f"{self.area_from_id} - {self.area_to_id}"

    @override
    def get_sub_id_for_aggregation(self) -> str | None:
        return None


@dataclass(frozen=True)
class AreaOutputIdentifier(SubAreaOutputIdentifier):
    query_file: Final[QueryFileType] = MCIndAreasQueryFile.VALUES

    @override
    def get_sub_id_for_aggregation(self) -> str | None:
        return None


def check_output_variable_exists(
    output_id: str,
    variable_type: OutputVariablesType,
    variable_name: str,
    available_variables: OutputVariablesList,
    output_identifier: OutputIdentifier,
) -> None:
    if variable_type == OutputVariablesType.LINK:
        assert isinstance(output_identifier, LinkOutputIdentifier)
        _checks_links_variables_view_coherence(output_id, available_variables, variable_name, output_identifier)

    else:
        _checks_areas_variables_view_coherence(
            output_id, available_variables, variable_name, output_identifier, variable_type
        )


def _checks_links_variables_view_coherence(
    output_id: str,
    available_variables: OutputVariablesList,
    variable_name: str,
    output_identifier: LinkOutputIdentifier,
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
    output_identifier: OutputIdentifier,
    variable_type: OutputVariablesType,
) -> None:
    area_id = output_identifier.get_id_for_aggregation()
    error_msg = f"The variable '{variable_name}' does not exist for area '{area_id}' and type '{variable_type.value}'"
    area_variables = available_variables.mc_ind.areas
    for area_variable in area_variables:
        if area_variable.name == area_id:
            match output_identifier:
                case AreaOutputIdentifier():
                    if variable_name in area_variable.variables:
                        return
                    raise OutputVariablesViewError(output_id, error_msg)
                case ThermalClusterOutputIdentifier():
                    variables = area_variable.thermal_clusters
                case RenewableClusterOutputIdentifier():
                    variables = area_variable.renewable_clusters
                case ShortTermStorageOutputIdentifier():
                    variables = area_variable.short_term_storages
                case _:
                    raise OutputVariablesViewError(output_id, error_msg)
            sub_id = output_identifier.get_sub_id_for_aggregation()
            for variable in variables:
                if variable.name == sub_id:
                    if variable_name in variable.variables:
                        return
                    raise OutputVariablesViewError(output_id, error_msg)

    raise OutputVariablesViewError(output_id, error_msg)


def check_arguments_coherence_and_return_identifier(
    variable_type: OutputVariablesType,
    output_id: str,
    area_id: str | None = None,
    area_from_id: str | None = None,
    area_to_id: str | None = None,
    thermal_id: str | None = None,
    renewable_id: str | None = None,
    st_storage_id: str | None = None,
) -> OutputIdentifier:
    if variable_type == OutputVariablesType.LINK:
        if any([area_id, thermal_id, renewable_id, st_storage_id]):
            raise OutputVariablesViewError(output_id, "You provided an area related id for links")
        if not area_from_id or not area_to_id:
            raise OutputVariablesViewError(
                output_id, "You should provide both `area_from_id` and `area_to_id` for links"
            )
        return LinkOutputIdentifier(area_from_id, area_to_id)

    if any([area_from_id, area_to_id]):
        raise OutputVariablesViewError(output_id, "You provided an link related id for areas")

    if not area_id:
        raise OutputVariablesViewError(output_id, "You should provide `area_id` for areas")

    if variable_type == OutputVariablesType.THERMAL:
        if not thermal_id:
            raise OutputVariablesViewError(output_id, "You should provide `thermal_id` for thermal clusters")
        if any([renewable_id, st_storage_id]):
            raise OutputVariablesViewError(output_id, "You provided an storage/renewable id for thermal clusters")
        return ThermalClusterOutputIdentifier(area_id, thermal_id)
    elif variable_type == OutputVariablesType.RENEWABLE:
        if not renewable_id:
            raise OutputVariablesViewError(output_id, "You should provide `renewable_id` for renewable clusters")
        if any([thermal_id, st_storage_id]):
            raise OutputVariablesViewError(output_id, "You provided an storage/thermal id for renewable clusters")
        return RenewableClusterOutputIdentifier(area_id, renewable_id)
    elif variable_type == OutputVariablesType.SHORT_TERM_STORAGE:
        if not st_storage_id:
            raise OutputVariablesViewError(output_id, "You should provide `st_storage_id` for short-term storages")
        if any([thermal_id, renewable_id]):
            raise OutputVariablesViewError(output_id, "You provided an renewable/thermal id for short-term storages")
        return ShortTermStorageOutputIdentifier(area_id, st_storage_id)
    else:
        if any([thermal_id, renewable_id, st_storage_id]):
            raise OutputVariablesViewError(output_id, "You provided an renewable/thermal/storage id for areas")
        return AreaOutputIdentifier(area_id)


def get_output_view_inside_db(
    study_id: str,
    output_id: str,
    variable_type: OutputVariablesType,
    variable_name: str,
    frequency: MatrixFrequency,
    output_identifier: OutputIdentifier,
) -> OutputVariablesViewsModel | None:
    q = db.session.query(OutputVariablesViewsModel)
    q = q.filter(OutputVariablesViewsModel.study_id == study_id)
    q = q.filter(OutputVariablesViewsModel.output_id == output_id)
    q = q.filter(OutputVariablesViewsModel.type == variable_type)
    q = q.filter(OutputVariablesViewsModel.frequency == frequency)
    q = q.filter(OutputVariablesViewsModel.variable_name == variable_name)

    match output_identifier:
        case AreaOutputIdentifier():
            filters = [(OutputVariablesViewsModel.area_id, output_identifier.get_id_for_aggregation())]
        case ThermalClusterOutputIdentifier():
            filters = [(OutputVariablesViewsModel.area_id, output_identifier.get_id_for_aggregation())]
            sub_id = output_identifier.get_sub_id_for_aggregation()
            assert sub_id is not None
            filters.append((OutputVariablesViewsModel.thermal_id, sub_id))
        case RenewableClusterOutputIdentifier():
            filters = [(OutputVariablesViewsModel.area_id, output_identifier.get_id_for_aggregation())]
            sub_id = output_identifier.get_sub_id_for_aggregation()
            assert sub_id is not None
            filters.append((OutputVariablesViewsModel.renewable_id, sub_id))
        case ShortTermStorageOutputIdentifier():
            filters = [(OutputVariablesViewsModel.area_id, output_identifier.get_id_for_aggregation())]
            sub_id = output_identifier.get_sub_id_for_aggregation()
            assert sub_id is not None
            filters.append((OutputVariablesViewsModel.st_storage_id, sub_id))
        case LinkOutputIdentifier():
            area_from_id, area_to_id = output_identifier.get_id_for_aggregation().split(" - ")
            filters = [(OutputVariablesViewsModel.area_from_id, area_from_id)]
            filters.append((OutputVariablesViewsModel.area_to_id, area_to_id))
        case _:
            raise NotImplementedError(f"output identifier `{output_identifier.__class__}` is not implemented")

    for column, value in filters:
        q = q.filter(column == value)

    return q.scalar()  # type: ignore


def create_output_view_db_model(
    study_id: str,
    output_id: str,
    variable_type: OutputVariablesType,
    variable_name: str,
    frequency: MatrixFrequency,
    output_identifier: OutputIdentifier,
    matrix_id: str,
) -> OutputVariablesViewsModel:
    model = OutputVariablesViewsModel(
        study_id=study_id,
        output_id=output_id,
        type=variable_type,
        frequency=frequency,
        variable_name=variable_name,
        matrix_id=matrix_id,
        last_read=current_time(),
    )

    match output_identifier:
        case AreaOutputIdentifier():
            model.area_id = output_identifier.get_id_for_aggregation()
        case ThermalClusterOutputIdentifier():
            model.area_id = output_identifier.get_id_for_aggregation()
            model.thermal_id = output_identifier.get_sub_id_for_aggregation()
        case RenewableClusterOutputIdentifier():
            model.area_id = output_identifier.get_id_for_aggregation()
            model.renewable_id = output_identifier.get_sub_id_for_aggregation()
        case ShortTermStorageOutputIdentifier():
            model.area_id = output_identifier.get_id_for_aggregation()
            model.st_storage_id = output_identifier.get_sub_id_for_aggregation()
        case LinkOutputIdentifier():
            area_from_id, area_to_id = output_identifier.get_id_for_aggregation().split(" - ")
            model.area_from_id = area_from_id
            model.area_to_id = area_to_id
        case _:
            raise NotImplementedError(f"output identifier `{output_identifier.__class__}` is not implemented")

    return model
