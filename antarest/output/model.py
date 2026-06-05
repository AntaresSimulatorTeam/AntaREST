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
from enum import StrEnum
from typing import Any, Callable, TypeVar

from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel

T = TypeVar("T")
Vars = TypeVar("Vars")
McIndVars = TypeVar("McIndVars")
McAllVars = TypeVar("McAllVars")


class _BaseModel(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    pass


class McIndVar(_BaseModel):
    """
    Metadata for an MC-ind variable. No stat here.
    """

    name: str
    unit: str | None


class McAllVar(_BaseModel):
    """
    Metadata for an MC-all variables. Adds stat: EXP, STD, etc.
    """

    name: str
    unit: str | None
    stat: str


class ComponentMcIndVariables(_BaseModel):
    """
    Mc-ind variables for one component (a thermal cluster, a renewable cluster, etc).
    """

    component_name: str
    variables: list[McIndVar]


class ComponentMcAllVariables(_BaseModel):
    """
    Mc-all (aggregated) variables for one component (a thermal cluster, a renewable cluster, etc).
    """

    component_name: str
    variables: list[McAllVar]


class ComponentVariableNames(_BaseModel):
    """
    Mc-ind variables for one component (a thermal cluster, a renewable cluster, etc).
    """

    name: str
    variables: list[str]


class AreaMcIndVariables(_BaseModel):
    """
    Mc-ind variables for one area, including variables of the components it contains.
    """

    area_name: str
    variables: list[McIndVar]
    thermal_clusters: list[ComponentMcIndVariables]
    renewable_clusters: list[ComponentMcIndVariables]
    short_term_storages: list[ComponentMcIndVariables]


class AreaMcAllVariables(_BaseModel):
    """
    Mc-all (aggregated) variables for one area, including variables of the components it contains.
    """

    area_name: str
    variables: list[McAllVar]
    thermal_clusters: list[ComponentMcAllVariables]
    renewable_clusters: list[ComponentMcAllVariables]
    short_term_storages: list[ComponentMcAllVariables]


class AreaVariableNames(_BaseModel):
    """
    Variable names for one area, including variables of the components it contains.
    """

    area_name: str
    variables: list[str]
    thermal_clusters: list[ComponentVariableNames]
    renewable_clusters: list[ComponentVariableNames]
    short_term_storages: list[ComponentVariableNames]


class LinkMcIndVariables(_BaseModel):
    area_1_name: str
    area_2_name: str
    variables: list[McIndVar]


class LinkMcAllVariables(_BaseModel):
    area_1_name: str
    area_2_name: str
    variables: list[McAllVar]


class LinkVariableNames(_BaseModel):
    area_1_name: str
    area_2_name: str
    variables: list[str]


class SystemMcIndVariables(_BaseModel):
    """
    mc-ind variables for the system as a whole
    """

    areas: list[AreaMcIndVariables]
    links: list[LinkMcIndVariables]


class SystemMcAllVariables(_BaseModel):
    """
    mc-all (aggregated) variables for the system as a whole
    """

    areas: list[AreaMcAllVariables]
    links: list[LinkMcAllVariables]


class SystemVariableNames(_BaseModel):
    areas: list[AreaVariableNames]
    links: list[LinkVariableNames]


class OutputVariablesList(_BaseModel):
    """
    Object representing the list of variables available for each item in the study.

    Since 8.6 and the introduction of free "groups" (of thermal clusters, for ex), the list
    of variables for an area can vary from one are to another.
    """

    mc_ind: SystemMcIndVariables
    mc_all: SystemMcAllVariables


class OutputVariableNames(_BaseModel):
    """
    Object representing the list of variables available for each item in the study.

    Since 8.6 and the introduction of free "groups" (of thermal clusters, for ex), the list
    of variables for an area can vary from one are to another.
    """

    mc_ind: SystemVariableNames
    mc_all: SystemVariableNames


def _convert_nested_dict(input: Any, mapper: Callable[[Any], Any]) -> Any:
    """utility convert some elements of a dictionary"""
    result = mapper(input)
    if result is not input:
        return result
    match input:
        case dict():
            return {k: _convert_nested_dict(v, mapper) for k, v in input.items()}
        case list():
            return [_convert_nested_dict(item, mapper) for item in input]
        case _:
            return input


def to_str_variables_list(variables_list: OutputVariablesList) -> OutputVariableNames:

    def mapper(obj: Any) -> Any:
        match obj:
            case McIndVar(name=name):
                return name
            case McAllVar(name=name, stat=stat):
                return " ".join((name, stat or ""))
            case {"name": name, "stat": stat} if set(obj) == {"name", "unit", "stat"}:
                return " ".join((name, stat or ""))
            case {"name": name} if set(obj) == {"name", "unit"}:
                return name
        return obj

    return OutputVariableNames.model_validate(_convert_nested_dict(variables_list.model_dump(mode="python"), mapper))


class OutputVariablesInformation(AntaresBaseModel, extra="forbid"):
    """
    Object representing the list of all variables available in an output.

    Before antares v8.6, the list of variables was the same for all areas and links,
    therefore that object was enough to know correctly which variables were available
    for any item in the study.
    Since 8.6 and the introduction of free "groups" (of thermal clusters, for ex), the list
    of variables for an area can vary from one are to another.
    Therefore, we now need a more complex object, see OutputVariablesList.
    """

    area: list[str]
    link: list[str]

    @staticmethod
    def from_variables_list(variables_list: OutputVariableNames) -> "OutputVariablesInformation":
        """
        Builds an OutputVariablesInformation by simply aggregating all variables of all areas and links.

        Hence, some areas or links may not actually contain any value for some of the variables.
        """
        args = {}

        # Areas
        all_area_variables = set()
        for area in variables_list.mc_ind.areas:
            all_area_variables.update(area.variables)
        args["area"] = sorted(all_area_variables)

        # Links
        all_link_variables = set()
        for link in variables_list.mc_ind.links:
            all_link_variables.update(link.variables)
        args["link"] = sorted(all_link_variables)

        return OutputVariablesInformation.model_validate(args)


class OutputVariablesType(StrEnum):
    AREA = "area"
    LINK = "link"
    THERMAL = "thermal"
    RENEWABLE = "renewable"
    SHORT_TERM_STORAGE = "st_storage"


class OutputVariablesViewStatus(StrEnum):
    NOT_FOUND = "NOT_FOUND"
    IN_PROGRESS = "IN_PROGRESS"


class OutputVariablesViewResponse(AntaresBaseModel, extra="forbid", alias_generator=to_camel, populate_by_name=True):
    status: OutputVariablesViewStatus
    task_id: str | None
