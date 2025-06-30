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

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, List, TypeVar

from antares.study.version import StudyVersion

from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.root.user.user import User


@dataclass(frozen=True)
class CommandOutput:
    status: bool
    message: str = ""


def command_failed(message: str) -> CommandOutput:
    return CommandOutput(False, message)


def command_succeeded(message: str) -> CommandOutput:
    return CommandOutput(True, message)


class FilteringOptions:
    FILTER_SYNTHESIS: str = "hourly, daily, weekly, monthly, annual"
    FILTER_YEAR_BY_YEAR: str = "hourly, daily, weekly, monthly, annual"


class CommandName(Enum):
    CREATE_AREA = "create_area"
    UPDATE_AREAS_PROPERTIES = "update_areas_properties"
    UPDATE_AREA_UI = "update_area_ui"
    REMOVE_AREA = "remove_area"
    CREATE_DISTRICT = "create_district"
    REMOVE_DISTRICT = "remove_district"
    CREATE_LINK = "create_link"
    UPDATE_LINK = "update_link"
    REMOVE_LINK = "remove_link"
    CREATE_BINDING_CONSTRAINT = "create_binding_constraint"
    UPDATE_BINDING_CONSTRAINT = "update_binding_constraint"
    REMOVE_BINDING_CONSTRAINT = "remove_binding_constraint"
    UPDATE_BINDING_CONSTRAINTS = "update_binding_constraints"
    REMOVE_MULTIPLE_BINDING_CONSTRAINTS = "remove_multiple_binding_constraints"
    CREATE_THERMAL_CLUSTER = "create_cluster"
    REMOVE_THERMAL_CLUSTER = "remove_cluster"
    UPDATE_THERMAL_CLUSTERS = "update_thermal_clusters"
    CREATE_RENEWABLES_CLUSTER = "create_renewables_cluster"
    REMOVE_RENEWABLES_CLUSTER = "remove_renewables_cluster"
    UPDATE_RENEWABLES_CLUSTERS = "update_renewables_clusters"
    CREATE_ST_STORAGE = "create_st_storage"
    REMOVE_ST_STORAGE = "remove_st_storage"
    REMOVE_MULTIPLE_ST_STORAGE_ADDITIONAL_CONSTRAINTS = "remove_st_storage_additional_constraints"
    UPDATE_ST_STORAGES = "update_st_storages"
    UPDATE_HYDRO_PROPERTIES = "update_hydro_properties"
    UPDATE_INFLOW_STRUCTURE = "update_inflow_structure"
    REPLACE_MATRIX = "replace_matrix"
    UPDATE_CONFIG = "update_config"
    UPDATE_COMMENTS = "update_comments"
    UPDATE_FILE = "update_file"
    UPDATE_DISTRICT = "update_district"
    UPDATE_PLAYLIST = "update_playlist"
    UPDATE_SCENARIO_BUILDER = "update_scenario_builder"
    GENERATE_THERMAL_CLUSTER_TIMESERIES = "generate_thermal_cluster_timeseries"
    CREATE_USER_RESOURCE = "create_user_resource"
    REMOVE_USER_RESOURCE = "remove_user_resource"
    REMOVE_XPANSION_CONFIGURATION = "remove_xpansion_configuration"
    REMOVE_XPANSION_RESOURCE = "remove_xpansion_resource"
    CREATE_XPANSION_CONFIGURATION = "create_xpansion_configuration"
    CREATE_XPANSION_CAPACITY = "create_xpansion_capacity"
    CREATE_XPANSION_WEIGHT = "create_xpansion_weight"
    CREATE_XPANSION_CONSTRAINT = "create_xpansion_constraint"
    CREATE_XPANSION_CANDIDATE = "create_xpansion_candidate"
    REMOVE_XPANSION_CANDIDATE = "remove_xpansion_candidate"
    REPLACE_XPANSION_CANDIDATE = "replace_xpansion_candidate"
    UPDATE_XPANSION_SETTINGS = "update_xpansion_settings"


def is_url_writeable(user_node: User, url: List[str]) -> bool:
    return url[0] not in [file.filename for file in user_node.registered_files]


T = TypeVar("T")


class IdMapping(Generic[T]):
    """
    This utility class performs several things:
        - It validates a file data: `data` via `func` and `study_version`
        - It constructs a mapping from the object id to the validated data
    """

    def __init__(
        self, func: Callable[[StudyVersion, Any], T], data: dict[str, dict[str, Any]], study_version: StudyVersion
    ) -> None:
        self.id_mapping: dict[str, tuple[str, T]] = {
            transform_name_to_id(k): (k, func(study_version, v)) for k, v in data.items()
        }

    def asserts_id_exists(self, id: str) -> bool:
        return id in self.id_mapping

    def get_key_and_properties(self, id: str) -> tuple[str, T]:
        return self.id_mapping[id]
