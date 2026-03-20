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
from typing import Annotated, Literal, Tuple, TypeAlias

from pydantic import BaseModel, Field

from antarest.core.exceptions import OutputVariablesViewError
from antarest.output.filestudy.utils import MCIndAreasQueryFile, MCIndLinksQueryFile, QueryFileType
from antarest.output.model import OutputVariablesList


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
