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
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

# First: input DTO
# Second: expected args after round trip or None if expecting same as input args
COMMANDS = [
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_AREA.value, args={"area_name": "area_name"}, study_version=STUDY_VERSION_8_8
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
            action=CommandName.UPDATE_AREA_UI.value,
            args={
                "area_id": "id",
                "area_ui": UpdateAreaUi(
                    x=100, y=100, color_rgb=(100, 100, 100), layer_x={}, layer_y={}, layer_color={}
                ),
                "layer": "0",
            },
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="update_area_ui",
    ),
    pytest.param(
        CommandDTO(action=CommandName.REMOVE_AREA.value, args={"id": "id"}, study_version=STUDY_VERSION_8_8),
        None,
        id="remove_area",
    ),
    pytest.param(
        CommandDTO(action=CommandName.REMOVE_AREA.value, args=[{"id": "id"}], study_version=STUDY_VERSION_8_8),
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
        CommandDTO(action=CommandName.REMOVE_DISTRICT.value, args={"id": "id"}, study_version=STUDY_VERSION_8_8),
        None,
        id="remove_district",
    ),
    pytest.param(
        CommandDTO(action=CommandName.REMOVE_DISTRICT.value, args=[{"id": "id"}], study_version=STUDY_VERSION_8_8),
        None,
        id="remove_district_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_LINK.value,
            args={
                "area1": "area1",
                "area2": "area2",
                "parameters": {},
                "series": "series",
            },
            study_version=STUDY_VERSION_8_8,
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
                    "parameters": {},
                    "series": "series",
                }
            ],
            study_version=STUDY_VERSION_8_8,
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
                    "parameters": {},
                    "series": "series",
                }
            ],
            study_version=STUDY_VERSION_8_8,
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
            action=CommandName.CREATE_BINDING_CONSTRAINT.value, args={"name": "name"}, study_version=STUDY_VERSION_8_8
        ),
        None,
        id="create_binding_constraint",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_BINDING_CONSTRAINT.value,
            args=[
                {
                    "name": "name",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "equal",
                    "values": "values",
                    "group": "group_1",
                },
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        None,
        id="create_binding_constraint_list",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
            args={
                "id": "id",
                "enabled": True,
                "time_step": "hourly",
                "operator": "equal",
                "values": "values",
            },
            study_version=STUDY_VERSION_8_8,
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
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "equal",
                }
            ],
            study_version=STUDY_VERSION_8_8,
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
        ),
        None,
        id="udpate_binding_constraints",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_BINDING_CONSTRAINT.value, args={"id": "id"}, study_version=STUDY_VERSION_8_8
        ),
        None,
        id="remove_binding_constraint",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.REMOVE_BINDING_CONSTRAINT.value, args=[{"id": "id"}], study_version=STUDY_VERSION_8_8
        ),
        None,
        id="remove_binding_constraint_list",
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
            version=2,
            args=[
                {
                    "area_id": "area_name",
                    "parameters": {
                        "name": "cluster_name",
                        "group": "nuclear",
                        "unitcount": 3,
                        "nominalcapacity": 100,
                        "marginal-cost": 40,
                        "market-bid-cost": 45,
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
                    "co2": 0.0,
                    "costgeneration": "SetManually",
                    "efficiency": 100.0,
                    "enabled": True,
                    "fixed-cost": 0.0,
                    "gen-ts": "use global",
                    "group": "nuclear",
                    "law.forced": "uniform",
                    "law.planned": "uniform",
                    "marginal-cost": 40.0,
                    "market-bid-cost": 45.0,
                    "min-down-time": 1,
                    "min-stable-power": 0.0,
                    "min-up-time": 1,
                    "must-run": False,
                    "name": "cluster_name",
                    "nh3": 0.0,
                    "nmvoc": 0.0,
                    "nominalcapacity": 100.0,
                    "nox": 0.0,
                    "op1": 0.0,
                    "op2": 0.0,
                    "op3": 0.0,
                    "op4": 0.0,
                    "op5": 0.0,
                    "pm10": 0.0,
                    "pm2_5": 0.0,
                    "pm5": 0.0,
                    "so2": 0.0,
                    "spinning": 0.0,
                    "spread-cost": 0.0,
                    "startup-cost": 0.0,
                    "unitcount": 3,
                    "variableomcost": 0.0,
                    "volatility.forced": 0.0,
                    "volatility.planned": 0.0,
                },
                "prepro": "prepro",
            }
        ],
        id="create_thermal_cluster_list",
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
            version=2,
            args={
                "area_id": "area_name",
                "parameters": {
                    "name": "cluster_name",
                    "ts-interpretation": "power-generation",
                },
            },
            study_version=STUDY_VERSION_8_8,
        ),
        {
            "area_id": "area_name",
            "parameters": {
                "enabled": True,
                "group": "other res 1",
                "name": "cluster_name",
                "nominalcapacity": 0.0,
                "ts-interpretation": "power-generation",
                "unitcount": 1,
            },
        },
        id="create_renewables_cluster",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
            version=2,
            args=[
                {
                    "area_id": "area_name",
                    "parameters": {
                        "name": "cluster_name",
                        "ts-interpretation": "power-generation",
                    },
                }
            ],
            study_version=STUDY_VERSION_8_8,
        ),
        [
            {
                "area_id": "area_name",
                "parameters": {
                    "enabled": True,
                    "group": "other res 1",
                    "name": "cluster_name",
                    "nominalcapacity": 0.0,
                    "ts-interpretation": "power-generation",
                    "unitcount": 1,
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
            action=CommandName.UPDATE_COMMENTS.value, args={"comments": "comments"}, study_version=STUDY_VERSION_8_8
        ),
        None,
        id="update_comments",
    ),
    pytest.param(
        CommandDTO(
            action=CommandName.UPDATE_COMMENTS.value, args=[{"comments": "comments"}], study_version=STUDY_VERSION_8_8
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
            version=2,
            args={
                "area_id": "area 1",
                "parameters": {
                    "name": "Storage 1",
                    "group": "Battery",
                    "injectionnominalcapacity": 0,
                    "withdrawalnominalcapacity": 0,
                    "reservoircapacity": 0,
                    "efficiency": 1,
                    "initiallevel": 0,
                    "initialleveloptim": False,
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
                "initiallevel": 0.0,
                "initialleveloptim": False,
                "injectionnominalcapacity": 0.0,
                "name": "Storage 1",
                "reservoircapacity": 0.0,
                "withdrawalnominalcapacity": 0.0,
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
            version=2,
            args=[
                {
                    "area_id": "area 1",
                    "parameters": {
                        "efficiency": 1,
                        "group": "Battery",
                        "initiallevel": 0,
                        "initialleveloptim": False,
                        "injectionnominalcapacity": 0,
                        "name": "Storage 1",
                        "reservoircapacity": 0,
                        "withdrawalnominalcapacity": 0,
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
                        "initiallevel": 0,
                        "initialleveloptim": False,
                        "injectionnominalcapacity": 0,
                        "name": "Storage 2",
                        "reservoircapacity": 0,
                        "withdrawalnominalcapacity": 0,
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
                    "initiallevel": 0.0,
                    "initialleveloptim": False,
                    "injectionnominalcapacity": 0.0,
                    "name": "Storage 1",
                    "reservoircapacity": 0.0,
                    "withdrawalnominalcapacity": 0.0,
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
                    "initiallevel": 0.0,
                    "initialleveloptim": False,
                    "injectionnominalcapacity": 0.0,
                    "name": "Storage 2",
                    "reservoircapacity": 0.0,
                    "withdrawalnominalcapacity": 0.0,
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
            action=CommandName.GENERATE_THERMAL_CLUSTER_TIMESERIES.value, args=[{}], study_version=STUDY_VERSION_8_8
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
]


@pytest.fixture
def command_factory() -> CommandFactory:
    def get_matrix_id(matrix: str) -> str:
        return matrix.removeprefix("matrix://")

    return CommandFactory(
        generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
        matrix_service=Mock(spec=MatrixService, get_matrix_id=get_matrix_id),
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
        self, command_dto: CommandDTO, expected_args: Optional[Dict[str, Any]], command_factory: CommandFactory
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
    assert dto.version == 2
    assert dto.args["parameters"]["name"] == "cluster_name"
    assert "cluster_name" not in dto.args


def test_parse_create_st_storage_dto_v1(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.CREATE_ST_STORAGE.value,
        version=1,
        args={
            "area_id": "area_name",
            "cluster_name": "cluster_name",
            "parameters": {
                "group": "Battery",
                "injectionnominalcapacity": 0,
                "withdrawalnominalcapacity": 0,
                "reservoircapacity": 0,
                "efficiency": 1,
                "initiallevel": 0,
                "initialleveloptim": False,
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
    assert dto.version == 2
    assert dto.args["parameters"]["name"] == "cluster_name"
    assert "cluster_name" not in dto.args


def test_parse_create_renewable_cluster_dto_v1(command_factory: CommandFactory):
    dto = CommandDTO(
        action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
        version=1,
        args={
            "area_id": "area_name",
            "cluster_name": "cluster_name",
            "parameters": {
                "ts-interpretation": "power-generation",
            },
        },
        study_version=STUDY_VERSION_8_8,
    )
    commands = command_factory.to_command(dto)
    assert len(commands) == 1
    command = commands[0]
    dto = command.to_dto()
    assert dto.version == 2
    assert dto.args["parameters"]["name"] == "cluster_name"
    assert "cluster_name" not in dto.args
