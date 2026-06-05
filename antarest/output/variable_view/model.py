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
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, Field

from antarest.core.exceptions import OutputVariablesViewError
from antarest.core.utils.collection_utils import find_if
from antarest.output.filestudy.utils import MCIndAreasQueryFile, MCIndLinksQueryFile, QueryFileType
from antarest.output.model import McIndVar, OutputVariablesList


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


def get_ids_for_aggregation(item_id: OutputItemId) -> tuple[str, str | None]:
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

    link_variable = find_if(link_variables, lambda lv: lv.area_1_name == area_from_id and lv.area_2_name == area_to_id)
    if not link_variable:
        raise OutputVariablesViewError(output_id, error_msg)
    if variable_name in map(lambda v: v.name, link_variable.variables):
        return
    raise OutputVariablesViewError(output_id, error_msg)


def _variable_exists(variables: list[McIndVar], variable_name: str) -> bool:
    return find_if(variables, lambda v: v.name == variable_name) is not None


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
    area_variables = find_if(available_variables.mc_ind.areas, lambda a: a.area_name == output_identifier.area_id)
    if not area_variables:
        raise OutputVariablesViewError(output_id, error_msg)

    match output_identifier:
        case AreaOutputId():
            if _variable_exists(area_variables.variables, variable_name):
                return
            raise OutputVariablesViewError(output_id, error_msg)
        case ThermalClusterOutputId():
            component_name = output_identifier.thermal_id
            variables = area_variables.thermal_clusters
        case RenewableClusterOutputId():
            component_name = output_identifier.renewable_id
            variables = area_variables.renewable_clusters
        case ShortTermStorageOutputId():
            component_name = output_identifier.st_storage_id
            variables = area_variables.short_term_storages
        case _:
            raise OutputVariablesViewError(output_id, error_msg)

    if comp_vars := find_if(variables, lambda v: v.component_name == component_name):
        if _variable_exists(comp_vars.variables, variable_name):
            return

    raise OutputVariablesViewError(output_id, error_msg)
