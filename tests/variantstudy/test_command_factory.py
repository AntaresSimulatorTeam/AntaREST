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

import importlib
import itertools
import pkgutil
from typing import Any, Dict, Optional, Set
from unittest.mock import Mock

import pytest

from antarest.matrixstore.service import MatrixService
from antarest.study.business.model.area_model import UpdateAreaUi
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

# First: input DTO
# Second: expected args after round trip or None if expecting same as input args
COMMANDS = [
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_AREA.value,
            args={"area_name": "area_name"},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="create_area",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_AREA.value,
            args=[
                {"area_name": "area_name"},
                {"area_name": "area2"},
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="create_area2",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_AREAS_PROPERTIES.value,
            args={"properties": {"fr": {"dispatch_hydro_power": True}}},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_areas_properties",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_AREA_UI.value,
            args={
                "area_id": "id",
                "area_ui": UpdateAreaUi(
                    x=100,
                    y=100,
                    color_rgb=(100, 100, 100),
                    layer_x={},
                    layer_y={},
                    layer_color={},
                ),
                "layer": "0",
            },
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_area_ui",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_AREA.value,
            args={"id": "id"},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_area",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_AREA.value,
            args=[{"id": "id"}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_area2",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_DISTRICT.value,
            args={
                "name": "id",
                "filter_items": ["a"],
                "output": True,
                "comments": "",
            },
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="create_district",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_DISTRICT.value,
            args=[
                {
                    "name": "id",
                    "base_filter": "add-all",
                    "output": True,
                    "comments": "",
                }
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="create_district_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_DISTRICT.value,
            args={"id": "id"},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_district",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_DISTRICT.value,
            args=[{"id": "id"}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_district_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_LINK.value,
            args={
                "area1": "area1",
                "area2": "area2",
                "parameters": {"hurdlesCost": False},
                "series": "series",
            },
            study_version=STUDY_VERSION_8_8,
            version=2,
        ),
        None,
        id="create_link",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_LINK.value,
            args=[
                {
                    "area1": "area1",
                    "area2": "area2",
                    "parameters": {"linkWidth": 0.4},
                    "series": "series",
                }
            ],
            study_version=STUDY_VERSION_8_8,
            version=2,
        ),
        None,
        id="create_link_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_LINK.value,
            args=[
                {
                    "area1": "area1",
                    "area2": "area2",
                    "parameters": {"usePhaseShifter": True},
                    "series": "series",
                }
            ],
            study_version=STUDY_VERSION_8_8,
            version=2,
        ),
        None,
        id="update_link",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_LINK.value,
            args={
                "area1": "area1",
                "area2": "area2",
            },
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_link",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_LINK.value,
            args=[
                {
                    "area1": "area1",
                    "area2": "area2",
                }
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_link_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_BINDING_CONSTRAINT.value,
            args={
                "matrices": {
                    "greaterTermMatrix": "matrix://fake_matrix",
                },
                "parameters": {
                    "enabled": False,
                    "filterSynthesis": "weekly",
                    "group": "group 1",
                    "name": "name",
                    "operator": "equal",
                    "timeStep": "hourly",
                },
            },
            study_version=STUDY_VERSION_8_8,
            version=2,
        ),
        None,
        id="create_binding_constraint",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_BINDING_CONSTRAINT.value,
            args=[
                {
                    "matrices": {
                        "equalTermMatrix": "matrix://fake_matrix",
                    },
                    "parameters": {"name": "name"},
                },
            ],
            study_version=STUDY_VERSION_8_8,
            version=2,
        ),
        None,
        id="create_binding_constraint_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
            args={
                "id": "id",
                "matrices": {"values": "values"},
                "parameters": {"enabled": True, "operator": "equal", "timeStep": "hourly"},
            },
            study_version=STUDY_VERSION_8_6,
            version=2,
        ),
        None,
        id="update_binding_constraint",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
            args=[
                {
                    "id": "id",
                    "matrices": {"lessTermMatrix": "matrix"},
                    "parameters": {
                        "enabled": True,
                        "filterSynthesis": "annual, weekly",
                        "timeStep": "daily",
                        "terms": [{"data": {"area1": "area1", "area2": "area2"}, "offset": 1, "weight": 4.2}],
                    },
                }
            ],
            study_version=STUDY_VERSION_8_8,
            version=2,
        ),
        None,
        id="udpate_binding_constraint_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_BINDING_CONSTRAINTS.value,
            args=[
                {
                    "bc_props_by_id": {
                        "id": {
                            "enabled": True,
                            "time_step": "hourly",
                            "operator": "equal",
                        }
                    }
                }
            ],
            study_version=STUDY_VERSION_8_8,
            version=2,
        ),
        None,
        id="udpate_binding_constraints",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_MULTIPLE_BINDING_CONSTRAINTS.value,
            args={"ids": ["id"]},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_multiple_constraints",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_MULTIPLE_BINDING_CONSTRAINTS.value,
            args=[{"ids": ["id"]}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_multiple_constraints_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_THERMAL_CLUSTER.value,
            version=3,
            args=[
                {
                    "area_id": "area_name",
                    "parameters": {
                        "name": "cluster_name",
                        "group": "nuclear",
                        "unitCount": 3,
                        "nominalCapacity": 100,
                        "marginalCost": 40,
                        "marketBidCost": 45,
                    },
                    "prepro": "prepro",
                    "modulation": "modulation",
                }
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        [
            {
                "area_id": "area_name",
                "modulation": "modulation",
                "parameters": {
                    "group": "nuclear",
                    "marginalCost": 40.0,
                    "marketBidCost": 45.0,
                    "name": "cluster_name",
                    "nominalCapacity": 100.0,
                    "unitCount": 3,
                },
                "prepro": "prepro",
            }
        ],
        id="create_thermal_cluster_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_THERMAL_CLUSTERS.value,
            args={
                "cluster_properties": {"area_name": {"cluster_name": {"efficiency": 90}}},
            },
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_thermal_clusters",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_THERMAL_CLUSTERS.value,
            args=[
                {
                    "cluster_properties": {"area_name": {"cluster_name": {"efficiency": 90}}},
                }
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_thermal_clusters_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_THERMAL_CLUSTER.value,
            args={"area_id": "area_name", "cluster_id": "cluster_name"},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_thermal_cluster",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_THERMAL_CLUSTER.value,
            args=[{"area_id": "area_name", "cluster_id": "cluster_name"}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_thermal_cluster_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
            version=3,
            args={
                "area_id": "area_name",
                "parameters": {
                    "name": "cluster_name",
                    "tsInterpretation": "power-generation",
                    "enabled": False,
                    "unitCount": 3,
                    "nominalCapacity": 100,
                    "group": "wind offshore",
                },
            },
            study_version=STUDY_VERSION_8_8,
        ),
        {
            "area_id": "area_name",
            "parameters": {
                "name": "cluster_name",
                "tsInterpretation": "power-generation",
                "enabled": False,
                "unitCount": 3,
                "nominalCapacity": 100,
                "group": "wind offshore",
            },
        },
        id="create_renewables_cluster",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
            version=3,
            args=[
                {
                    "area_id": "area_name",
                    "parameters": {"name": "cluster_name", "enabled": False, "unitCount": 4},
                }
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        [
            {
                "area_id": "area_name",
                "parameters": {
                    "enabled": False,
                    "name": "cluster_name",
                    "unitCount": 4,
                },
            }
        ],
        id="create_renewables_cluster_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_RENEWABLES_CLUSTER.value,
            args={"area_id": "area_name", "cluster_id": "cluster_name"},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_renewables_cluster",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_RENEWABLES_CLUSTER.value,
            args=[{"area_id": "area_name", "cluster_id": "cluster_name"}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_renewables_cluster_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_RENEWABLES_CLUSTERS.value,
            args=[{"cluster_properties": {"area_name": {"cluster_name": {"unit_count": 10}}}}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_renewable_clusters",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REPLACE_MATRIX.value,
            args={"target": "target_element", "matrix": "matrix"},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="replace_matrix",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REPLACE_MATRIX.value,
            args=[{"target": "target_element", "matrix": "matrix"}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="replace_matrix_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_CONFIG.value,
            args={"target": "target", "data": {}},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_config",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_CONFIG.value,
            args=[{"target": "target", "data": {}}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_config_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_COMMENTS.value,
            args={"comments": "comments"},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_comments",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_COMMENTS.value,
            args=[{"comments": "comments"}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_comments_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_FILE.value,
            args={
                "target": "settings/resources/study",
                "b64Data": "",
            },
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_file",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_DISTRICT.value,
            args={"id": "id", "filter_items": ["a"]},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_district",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_DISTRICT.value,
            args=[{"id": "id", "base_filter": "add-all"}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_district_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_PLAYLIST.value,
            args=[{"active": True, "items": [1, 3], "reverse": False}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_playlist_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_PLAYLIST.value,
            args={
                "active": True,
                "items": [1, 3],
                "weights": {1: 5.0},
                "reverse": False,
            },
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_playlist",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_SCENARIO_BUILDER.value,
            args={
                "data": {
                    "ruleset test": {
                        "l": {"area1": {"0": 1}},
                        "ntc": {"area1 / area2": {"1": 23}},
                        "t": {"area1": {"thermal": {"1": 2}}},
                    },
                }
            },
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_scenario_builder",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_ST_STORAGE.value,
            version=3,
            args={
                "area_id": "area 1",
                "parameters": {
                    "name": "Storage 1",
                    "group": "Battery",
                    "enabled": True,
                    "injectionNominalCapacity": 0,
                    "withdrawalNominalCapacity": 0,
                    "reservoirCapacity": 0,
                    "efficiency": 1,
                    "initialLevel": 0,
                    "initialLevelOptim": False,
                },
                "pmax_injection": "matrix://59ea6c83-6348-466d-9530-c35c51ca4c37",
                "pmax_withdrawal": "matrix://5f988548-dadc-4bbb-8ce8-87a544dbf756",
                "lower_rule_curve": "matrix://8ce4fcea-cc97-4d2c-b641-a27a53454612",
                "upper_rule_curve": "matrix://8ce614c8-c687-41af-8b24-df8a49cc52af",
                "inflows": "matrix://df9b25e1-e3f7-4a57-8182-0ff9791439e5",
            },
            study_version=STUDY_VERSION_8_8,
        ),
        {
            "area_id": "area 1",
            "inflows": "matrix://df9b25e1-e3f7-4a57-8182-0ff9791439e5",
            "lower_rule_curve": "matrix://8ce4fcea-cc97-4d2c-b641-a27a53454612",
            "parameters": {
                "efficiency": 1.0,
                "enabled": True,
                "group": "battery",
                "initialLevel": 0.0,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 0.0,
                "name": "Storage 1",
                "reservoirCapacity": 0.0,
                "withdrawalNominalCapacity": 0.0,
            },
            "pmax_injection": "matrix://59ea6c83-6348-466d-9530-c35c51ca4c37",
            "pmax_withdrawal": "matrix://5f988548-dadc-4bbb-8ce8-87a544dbf756",
            "upper_rule_curve": "matrix://8ce614c8-c687-41af-8b24-df8a49cc52af",
        },
        id="create_st_storage",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_ST_STORAGE.value,
            version=3,
            args=[
                {
                    "area_id": "area 1",
                    "parameters": {
                        "efficiency": 1,
                        "group": "Battery",
                        "enabled": True,
                        "initialLevel": 0,
                        "initialLevelOptim": False,
                        "injectionNominalCapacity": 0,
                        "name": "Storage 1",
                        "reservoirCapacity": 0,
                        "withdrawalNominalCapacity": 0,
                    },
                    "pmax_injection": "matrix://59ea6c83-6348-466d-9530-c35c51ca4c37",
                    "pmax_withdrawal": "matrix://5f988548-dadc-4bbb-8ce8-87a544dbf756",
                    "lower_rule_curve": "matrix://8ce4fcea-cc97-4d2c-b641-a27a53454612",
                    "upper_rule_curve": "matrix://8ce614c8-c687-41af-8b24-df8a49cc52af",
                    "inflows": "matrix://df9b25e1-e3f7-4a57-8182-0ff9791439e5",
                },
                {
                    "area_id": "area 1",
                    "parameters": {
                        "efficiency": 0.94,
                        "group": "Battery",
                        "enabled": True,
                        "initialLevel": 0,
                        "initialLevelOptim": False,
                        "injectionNominalCapacity": 0,
                        "name": "Storage 2",
                        "reservoirCapacity": 0,
                        "withdrawalNominalCapacity": 0,
                    },
                    "pmax_injection": "matrix://3f5b3746-3995-49b7-a6da-622633472e05",
                    "pmax_withdrawal": "matrix://4b64a31f-927b-4887-b4cd-adcddd39bdcd",
                    "lower_rule_curve": "matrix://16c7c3ae-9824-4ef2-aa68-51145884b025",
                    "upper_rule_curve": "matrix://9a6104e9-990a-415f-a6e2-57507e13b58c",
                    "inflows": "matrix://e8923768-9bdd-40c2-a6ea-2da2523be727",
                },
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        [
            {
                "area_id": "area 1",
                "inflows": "matrix://df9b25e1-e3f7-4a57-8182-0ff9791439e5",
                "lower_rule_curve": "matrix://8ce4fcea-cc97-4d2c-b641-a27a53454612",
                "parameters": {
                    "efficiency": 1.0,
                    "enabled": True,
                    "group": "battery",
                    "initialLevel": 0.0,
                    "initialLevelOptim": False,
                    "injectionNominalCapacity": 0.0,
                    "name": "Storage 1",
                    "reservoirCapacity": 0.0,
                    "withdrawalNominalCapacity": 0.0,
                },
                "pmax_injection": "matrix://59ea6c83-6348-466d-9530-c35c51ca4c37",
                "pmax_withdrawal": "matrix://5f988548-dadc-4bbb-8ce8-87a544dbf756",
                "upper_rule_curve": "matrix://8ce614c8-c687-41af-8b24-df8a49cc52af",
            },
            {
                "area_id": "area 1",
                "inflows": "matrix://e8923768-9bdd-40c2-a6ea-2da2523be727",
                "lower_rule_curve": "matrix://16c7c3ae-9824-4ef2-aa68-51145884b025",
                "parameters": {
                    "efficiency": 0.94,
                    "enabled": True,
                    "group": "battery",
                    "initialLevel": 0.0,
                    "initialLevelOptim": False,
                    "injectionNominalCapacity": 0.0,
                    "name": "Storage 2",
                    "reservoirCapacity": 0.0,
                    "withdrawalNominalCapacity": 0.0,
                },
                "pmax_injection": "matrix://3f5b3746-3995-49b7-a6da-622633472e05",
                "pmax_withdrawal": "matrix://4b64a31f-927b-4887-b4cd-adcddd39bdcd",
                "upper_rule_curve": "matrix://9a6104e9-990a-415f-a6e2-57507e13b58c",
            },
        ],
        id="create_st_storage_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_ST_STORAGE.value,
            args={
                "area_id": "area 1",
                "storage_id": "storage 1",
            },
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_st_storage",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_ST_STORAGE.value,
            args=[
                {
                    "area_id": "area 1",
                    "storage_id": "storage 1",
                },
                {
                    "area_id": "area 1",
                    "storage_id": "storage 2",
                },
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_st_storage_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_ST_STORAGES.value,
            args={"storage_properties": {"area 1": {"sts_1": {"enabled": False}}}},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_st_storages",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.GENERATE_THERMAL_CLUSTER_TIMESERIES.value,
            args=[{}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="generate_thermal_cluster_timeseries_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_USER_RESOURCE.value,
            args=[{"data": {"path": "folder_1", "resource_type": "folder"}}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="create_user_resource_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_USER_RESOURCE.value,
            args=[{"data": {"path": "folder_1"}}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_user_resource_list_folder",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_USER_RESOURCE.value,
            args=[{"data": {"path": "file_1.txt"}}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_user_resource_list_file",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_XPANSION_CANDIDATE.value,
            args=[{"candidate": {"name": "cdt_1", "link": "at - be", "annual-cost-per-mw": 12, "max-investment": 100}}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="create_xpansion_candidate",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REPLACE_XPANSION_CANDIDATE.value,
            args=[
                {
                    "candidate_name": "cdt_1",
                    "properties": {
                        "name": "cdt_1",
                        "link": "at - be",
                        "annual-cost-per-mw": 12,
                        "max-investment": 100,
                    },
                }
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_xpansion_candidate",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_XPANSION_CANDIDATE.value,
            args=[{"candidate_name": "cdt_1"}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="remove_xpansion_candidate",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_HYDRO_PROPERTIES.value,
            args={"area_id": "area_name", "properties": {"reservoir_capacity": 0.5}},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_hydro_properties",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_INFLOW_STRUCTURE.value,
            args={"area_id": "area_name", "properties": {"inter_monthly_correlation": 0.5}},
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_inflow_structure",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_XPANSION_SETTINGS.value,
            args=[{"settings": {"master": "integer", "max_iteration": 44}}],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_xpansion_settings",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_ST_STORAGE_ADDITIONAL_CONSTRAINTS.value,
            args=[
                {
                    "area_id": "fr",
                    "storage_id": "sts_2",
                    "constraints": [
                        {
                            "name": "c3",
                            "variable": "withdrawal",
                            "operator": "greater",
                            "hours": "[1, 2, 3, 4], [12, 13]",
                        }
                    ],
                }
            ],
            study_version=STUDY_VERSION_9_2,
        ),
        None,
        id="create_st_storage_additional_constraints",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_ST_STORAGE_ADDITIONAL_CONSTRAINTS.value,
            args=[
                {"additional_constraint_properties": {"fr": {"sts_2": [{"id": "c1"}]}}},
            ],
            study_version=STUDY_VERSION_9_2,
        ),
        None,
        id="update_st_storage_additional_constraints",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_MULTIPLE_ST_STORAGE_ADDITIONAL_CONSTRAINTS.value,
            args=[
                {"area_id": "fr", "ids": ["c1", "c2", "c3"]},
            ],
            study_version=STUDY_VERSION_9_2,
        ),
        None,
        id="remove_st_storage_additional_constraints",
    ),
]


@pytest.fixture
def command_factory() -> CommandFactory:
    def get_matrix_id(matrix: str) -> str:
        return matrix.removeprefix("matrix://")

    matrix_service = Mock(spec=MatrixService, get_matrix_id=get_matrix_id)

    class FakeGeneratorMatrixConstants(GeneratorMatrixConstants):
        """Made to avoid having Mock objects in commands arguments"""

        def __getattribute__(self, name):
            if name in ("_return_value", "__class__"):  # Avoid infinite loop
                return super().__getattribute__(name)
            return lambda *args, **kwargs: "fake_matrix"

    return CommandFactory(
        generator_matrix_constants=FakeGeneratorMatrixConstants(matrix_service),
        matrix_service=matrix_service,
    )


class TestCommandFactory:
    def _get_command_classes(self) -> Set[str]:
        """
        Imports all modules from the `antarest.study.storage.variantstudy.model.command` package
        and creates a set of command class names derived from the `ICommand` abstract class.
        The objective is to ensure that the unit test covers all commands in this package.
        """
        for module_loader, name, ispkg in pkgutil.iter_modules(["antarest/study/storage/variantstudy/model/command"]):
            importlib.import_module(
                f".{name}",
                package="antarest.study.storage.variantstudy.model.command",
            )
        abstract_commands = {"AbstractBindingConstraintCommand", "AbstractLinkCommand"}
        return {cmd.__name__ for cmd in ICommand.__subclasses__() if cmd.__name__ not in abstract_commands}

    # noinspection SpellCheckingInspection
    @pytest.mark.parametrize(
        ["command_dto", "expected_args"],
        COMMANDS,
    )
    @pytest.mark.unit_test
    def test_command_factory(
        self,
        command_dto: CommandDTO,
        expected_args: Optional[Dict[str, Any]],
        command_factory: CommandFactory,
    ):
        commands = command_factory.to_command(command_dto=command_dto)

        expected_args = expected_args or command_dto.args
        if isinstance(expected_args, dict):
            exp_action_args_list = [(command_dto.action, expected_args, command_dto.version)]
        else:
            exp_action_args_list = [(command_dto.action, args, command_dto.version) for args in expected_args]

        actual_cmd: ICommand
        for actual_cmd, exp_action_args_version in itertools.zip_longest(commands, exp_action_args_list):
            assert actual_cmd is not None, f"Missing action/args for {exp_action_args_version=}"
            assert exp_action_args_version is not None, f"Missing command for {actual_cmd=}"
            expected_action, expected_args, expected_version = exp_action_args_version
            actual_dto = actual_cmd.to_dto()
            actual_args = {k: v for k, v in actual_dto.args.items() if v is not None}
            actual_version = actual_dto.version
            assert actual_dto.action == expected_action
            assert actual_args == expected_args
            assert actual_version == expected_version


@pytest.mark.unit_test
def test_unknown_command():
    with pytest.raises(NotImplementedError):
        command_factory = CommandFactory(
            generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
            matrix_service=Mock(spec=MatrixService),
        )
        command_factory.to_command(
            command_dto=CommandDTO(action="unknown_command", args={}, study_version=STUDY_VERSION_8_8)
        )


@pytest.mark.unit_test
def test_parse_create_cluster_dto_v1(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.CREATE_THERMAL_CLUSTER.value,
        version=1,
        args={
            "area_id": "area_name",
            "cluster_name": "cluster_name",
            "parameters": {},
            "prepro": "prepro",
            "modulation": "modulation",
        },
        study_version=STUDY_VERSION_8_8,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.version == 3
    assert dto.args["parameters"]["name"] == "cluster_name"
    assert "cluster_name" not in dto.args


@pytest.mark.unit_test
def test_parse_create_cluster_dto_v2(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.CREATE_THERMAL_CLUSTER.value,
        version=2,
        args={
            "area_id": "area_name",
            "parameters": {"name": "cluster_name"},
            "prepro": "prepro",
            "modulation": "modulation",
        },
        study_version=STUDY_VERSION_8_8,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.version == 3
    assert dto.args["parameters"]["name"] == "cluster_name"
    assert "cluster_name" not in dto.args


def test_parse_create_st_storage_dto_v1(command_factory: CommandFactory):
    dto = CommandDTO(
        id="9f01931b-0f18-4477-9ef4-ac682c970d75",
        action=CommandName.CREATE_ST_STORAGE.value,
        version=1,
        args={
            "area_id": "area_name",
            "parameters": {
                "name": "battery storage_2 candidate",
                "group": "Battery",
                "injectionnominalcapacity": 0,
                "withdrawalnominalcapacity": 0,
                "reservoircapacity": 0,
                "efficiency": 1,
                "initiallevel": 0,
                "initialleveloptim": False,
                "enabled": True,
            },
            "pmax_injection": "matrix://59ea6c83-6348-466d-9530-c35c51ca4c37",
            "pmax_withdrawal": "matrix://5f988548-dadc-4bbb-8ce8-87a544dbf756",
            "lower_rule_curve": "matrix://8ce4fcea-cc97-4d2c-b641-a27a53454612",
            "upper_rule_curve": "matrix://8ce614c8-c687-41af-8b24-df8a49cc52af",
            "inflows": "matrix://df9b25e1-e3f7-4a57-8182-0ff9791439e5",
        },
        study_version=STUDY_VERSION_8_8,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.version == 3
    assert dto.args["parameters"]["name"] == "battery storage_2 candidate"


def test_parse_create_renewable_cluster_dto_v1(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
        version=1,
        args={
            "area_id": "area_name",
            "cluster_name": "cluster_name",
            "parameters": {"ts-interpretation": "power-generation"},
        },
        study_version=STUDY_VERSION_8_8,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.version == 3
    assert dto.args["parameters"]["name"] == "cluster_name"
    assert "cluster_name" not in dto.args


def test_parse_create_renewable_cluster_dto_v2(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
        version=2,
        args={"area_id": "area_name", "parameters": {"name": "Sts_1", "ts-interpretation": "power-generation"}},
        study_version=STUDY_VERSION_8_8,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.version == 3
    assert dto.args["parameters"]["name"] == "Sts_1"
    assert dto.args["parameters"]["tsInterpretation"] == "power-generation"
    assert "cluster_name" not in dto.args


def test_parse_create_link_dto_v1(command_factory: CommandFactory):
    for parameters in [{"link-width": 0.56}, None]:  # legacy cases
        dto = CommandDTO(
            action=CommandName.CREATE_LINK.value,
            version=1,
            args={"area1": "area1", "area2": "area2", "parameters": parameters},
            study_version=STUDY_VERSION_8_8,
        )
        commands = command_factory.to_command(dto)
        assert len(commands) == 1
        command = commands[0]
        dto = command.to_dto()
        assert dto.version == 2
        if parameters is None:
            assert dto.args["parameters"] == {}
        else:
            assert dto.args["parameters"]["linkWidth"] == 0.56


def test_parse_create_binding_constraint_dto_v1(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.CREATE_BINDING_CONSTRAINT.value,
        args=[
            {
                "name": "name",
                "enabled": True,
                "time_step": "hourly",
                "operator": "equal",
                "less_term_matrix": "matrix",
                "group": "group_1",
            },
        ],
        study_version=STUDY_VERSION_8_8,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.version == 2
    assert dto.args == {
        "matrices": {
            "lessTermMatrix": "matrix://matrix",
        },
        "parameters": {
            "comments": "",
            "enabled": True,
            "filterSynthesis": "",
            "filterYearByYear": "",
            "group": "group_1",
            "name": "name",
            "operator": "equal",
            "terms": [],
            "timeStep": "hourly",
        },
    }


def test_parse_update_binding_constraint_dto_v1(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
        args={
            "id": "id",
            "enabled": True,
            "time_step": "hourly",
            "operator": "equal",
            "values": "values",
            "coeffs": {"area1.cluster_x": [1, 2]},
        },
        study_version=STUDY_VERSION_8_6,
        version=1,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.version == 2
    assert dto.args == {
        "id": "id",
        "matrices": {"values": "values"},
        "parameters": {
            "enabled": True,
            "operator": "equal",
            "timeStep": "hourly",
            "terms": [{"data": {"area": "area1", "cluster": "cluster_x"}, "offset": 2, "weight": 1.0}],
        },
    }


def test_parse_update_binding_constraints_dto_v1(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.UPDATE_BINDING_CONSTRAINTS.value,
        args={
            "bc_props_by_id": {
                "bc_1": {
                    "enabled": False,
                    "time_step": "weekly",
                    "operator": "both",
                    "comments": "Hello !",
                    "filter_year_by_year": "annual, hourly",
                }
            }
        },
        study_version=STUDY_VERSION_8_8,
        version=1,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.version == 2
    assert dto.args == {
        "bc_props_by_id": {
            "bc_1": {
                "comments": "Hello !",
                "enabled": False,
                "filter_year_by_year": "annual, hourly",
                "operator": "both",
                "time_step": "weekly",
            }
        }
    }


def test_parse_legacy_command_remove_binding_constraint(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.REMOVE_BINDING_CONSTRAINT.value,
        args={"id": "id"},
        study_version=STUDY_VERSION_8_6,
        version=1,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.action == "remove_multiple_binding_constraints"
    assert dto.version == 1
    assert dto.args == {"ids": ["id"]}
