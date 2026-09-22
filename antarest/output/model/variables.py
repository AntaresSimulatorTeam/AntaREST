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
from typing import Annotated, TypeAlias

from pydantic import BeforeValidator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel

Variables: TypeAlias = Annotated[list[str], BeforeValidator(lambda x: sorted(x))]


class AreaClusterVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    name: str
    variables: Variables = []


ClusterVariables: TypeAlias = Annotated[
    list[AreaClusterVariables], BeforeValidator(lambda x: sorted(x, key=lambda a: a["name"]))
]


class AreaVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    name: str
    variables: Variables = []
    thermal_clusters: ClusterVariables = []
    renewable_clusters: ClusterVariables = []
    short_term_storages: ClusterVariables = []


class LinkVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    area_1_name: str
    area_2_name: str
    variables: Variables = []


class AreaAndLinkVariables(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    areas: list[AreaVariables]
    links: list[LinkVariables]


class OutputVariablesList(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    mc_ind: AreaAndLinkVariables
    mc_all: AreaAndLinkVariables


class OutputVariablesInformation(AntaresBaseModel, extra="forbid"):
    area: list[str]
    link: list[str]

    @staticmethod
    def from_variables_list(variables_list: OutputVariablesList) -> "OutputVariablesInformation":
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
