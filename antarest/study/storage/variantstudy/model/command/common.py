# Copyright (c) 2024, RTE (https://www.rte-france.com)
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


@dataclass
class CommandOutput:
    status: bool
    message: str = ""


class FilteringOptions:
    FILTER_SYNTHESIS: str = "hourly, daily, weekly, monthly, annual"
    FILTER_YEAR_BY_YEAR: str = "hourly, daily, weekly, monthly, annual"


class CommandName(Enum):
    CREATE_AREA = "create_area"
    REMOVE_AREA = "remove_area"
    CREATE_DISTRICT = "create_district"
    REMOVE_DISTRICT = "remove_district"
    CREATE_LINK = "create_link"
    REMOVE_LINK = "remove_link"
    CREATE_BINDING_CONSTRAINT = "create_binding_constraint"
    UPDATE_BINDING_CONSTRAINT = "update_binding_constraint"
    REMOVE_BINDING_CONSTRAINT = "remove_binding_constraint"
    CREATE_THERMAL_CLUSTER = "create_cluster"
    REMOVE_THERMAL_CLUSTER = "remove_cluster"
    CREATE_RENEWABLES_CLUSTER = "create_renewables_cluster"
    REMOVE_RENEWABLES_CLUSTER = "remove_renewables_cluster"
    CREATE_ST_STORAGE = "create_st_storage"
    REMOVE_ST_STORAGE = "remove_st_storage"
    REPLACE_MATRIX = "replace_matrix"
    UPDATE_CONFIG = "update_config"
    UPDATE_COMMENTS = "update_comments"
    UPDATE_FILE = "update_file"
    UPDATE_DISTRICT = "update_district"
    UPDATE_PLAYLIST = "update_playlist"
    UPDATE_SCENARIO_BUILDER = "update_scenario_builder"
    GENERATE_THERMAL_CLUSTER_TIMESERIES = "generate_thermal_cluster_timeseries"
    CREATE_USER_FOLDER = "create_user_folder"
    REMOVE_USER_FOLDER = "remove_user_folder"
    REMOVE_USER_FILE = "remove_user_file"
