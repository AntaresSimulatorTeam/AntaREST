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

import copy
from dataclasses import dataclass
from typing import Dict, List, Optional, Type

from antares.study.version import StudyVersion

from antarest.core.model import JSON
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.create_district import CreateDistrict
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.create_user_resource import CreateUserResource
from antarest.study.storage.variantstudy.model.command.create_xpansion_configuration import CreateXpansionConfiguration
from antarest.study.storage.variantstudy.model.command.generate_thermal_cluster_timeseries import (
    GenerateThermalClusterTimeSeries,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import RemoveBindingConstraint
from antarest.study.storage.variantstudy.model.command.remove_cluster import RemoveCluster
from antarest.study.storage.variantstudy.model.command.remove_district import RemoveDistrict
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.remove_multiple_binding_constraints import (
    RemoveMultipleBindingConstraints,
)
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import RemoveRenewablesCluster
from antarest.study.storage.variantstudy.model.command.remove_st_storage import RemoveSTStorage
from antarest.study.storage.variantstudy.model.command.remove_user_resource import RemoveUserResource
from antarest.study.storage.variantstudy.model.command.remove_xpansion_configuration import RemoveXpansionConfiguration
from antarest.study.storage.variantstudy.model.command.remove_xpansion_resource import RemoveXpansionResource
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_area_ui import UpdateAreaUI
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint
from antarest.study.storage.variantstudy.model.command.update_comments import UpdateComments
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_district import UpdateDistrict
from antarest.study.storage.variantstudy.model.command.update_link import UpdateLink
from antarest.study.storage.variantstudy.model.command.update_playlist import UpdatePlaylist
from antarest.study.storage.variantstudy.model.command.update_raw_file import UpdateRawFile
from antarest.study.storage.variantstudy.model.command.update_renewable_cluster import UpdateRenewableCluster
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command.update_st_storage import UpdateSTStorage
from antarest.study.storage.variantstudy.model.command.update_thermal_cluster import UpdateThermalCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.model import CommandDTO

COMMAND_MAPPING: Dict[str, Type[ICommand]] = {
    CommandName.CREATE_AREA.value: CreateArea,
    CommandName.UPDATE_AREA_UI.value: UpdateAreaUI,
    CommandName.REMOVE_AREA.value: RemoveArea,
    CommandName.CREATE_DISTRICT.value: CreateDistrict,
    CommandName.REMOVE_DISTRICT.value: RemoveDistrict,
    CommandName.CREATE_LINK.value: CreateLink,
    CommandName.UPDATE_LINK.value: UpdateLink,
    CommandName.REMOVE_LINK.value: RemoveLink,
    CommandName.CREATE_BINDING_CONSTRAINT.value: CreateBindingConstraint,
    CommandName.UPDATE_BINDING_CONSTRAINT.value: UpdateBindingConstraint,
    CommandName.REMOVE_BINDING_CONSTRAINT.value: RemoveBindingConstraint,
    CommandName.REMOVE_MULTIPLE_BINDING_CONSTRAINTS.value: RemoveMultipleBindingConstraints,
    CommandName.CREATE_THERMAL_CLUSTER.value: CreateCluster,
    CommandName.REMOVE_THERMAL_CLUSTER.value: RemoveCluster,
    CommandName.UPDATE_THERMAL_CLUSTER.value: UpdateThermalCluster,
    CommandName.CREATE_RENEWABLES_CLUSTER.value: CreateRenewablesCluster,
    CommandName.REMOVE_RENEWABLES_CLUSTER.value: RemoveRenewablesCluster,
    CommandName.UPDATE_RENEWABLE_CLUSTER.value: UpdateRenewableCluster,
    CommandName.CREATE_ST_STORAGE.value: CreateSTStorage,
    CommandName.REMOVE_ST_STORAGE.value: RemoveSTStorage,
    CommandName.UPDATE_ST_STORAGE.value: UpdateSTStorage,
    CommandName.REPLACE_MATRIX.value: ReplaceMatrix,
    CommandName.UPDATE_CONFIG.value: UpdateConfig,
    CommandName.UPDATE_COMMENTS.value: UpdateComments,
    CommandName.UPDATE_FILE.value: UpdateRawFile,
    CommandName.UPDATE_DISTRICT.value: UpdateDistrict,
    CommandName.UPDATE_PLAYLIST.value: UpdatePlaylist,
    CommandName.UPDATE_SCENARIO_BUILDER.value: UpdateScenarioBuilder,
    CommandName.GENERATE_THERMAL_CLUSTER_TIMESERIES.value: GenerateThermalClusterTimeSeries,
    CommandName.CREATE_USER_RESOURCE.value: CreateUserResource,
    CommandName.REMOVE_USER_RESOURCE.value: RemoveUserResource,
    CommandName.REMOVE_XPANSION_CONFIGURATION.value: RemoveXpansionConfiguration,
    CommandName.CREATE_XPANSION_CONFIGURATION.value: CreateXpansionConfiguration,
    CommandName.REMOVE_XPANSION_RESOURCE.value: RemoveXpansionResource,
}


@dataclass(frozen=True)
class CommandValidationContext:
    version: int


class CommandFactory:
    """
    Service to convert CommendDTO to Command
    """

    def __init__(
        self,
        generator_matrix_constants: GeneratorMatrixConstants,
        matrix_service: ISimpleMatrixService,
    ):
        self.command_context = CommandContext(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=matrix_service,
        )

    def _to_single_command(
        self, action: str, args: JSON, version: int, study_version: StudyVersion, command_id: Optional[str]
    ) -> ICommand:
        """Convert a single CommandDTO to ICommand."""
        if action in COMMAND_MAPPING:
            command_class = COMMAND_MAPPING[action]
            data = copy.deepcopy(args)
            data.update(
                {
                    "command_context": self.command_context,
                    "command_id": command_id,
                    "study_version": study_version,
                }
            )
            return command_class.model_validate(data, context=CommandValidationContext(version=version))
        raise NotImplementedError(action)

    def to_command(self, command_dto: CommandDTO) -> List[ICommand]:
        """
        Convert a CommandDTO to a list of ICommand.

        Args:
            command_dto: The CommandDTO to convert.

        Returns:
            List: A list of ICommand instances.

        Raises:
            NotImplementedError: If the argument type is not implemented.
        """
        args = command_dto.args
        if isinstance(args, dict):
            # In some cases, pydantic can modify inplace the given args.
            # We don't want that so before doing so we copy the dictionary.
            new_args = copy.deepcopy(args)
            return [
                self._to_single_command(
                    command_dto.action, new_args, command_dto.version, command_dto.study_version, command_dto.id
                )
            ]
        elif isinstance(args, list):
            return [
                self._to_single_command(
                    command_dto.action,
                    copy.deepcopy(argument),
                    command_dto.version,
                    command_dto.study_version,
                    command_dto.id,
                )
                for argument in args
            ]
        raise NotImplementedError()

    def to_commands(self, cmd_dto_list: List[CommandDTO]) -> List[ICommand]:
        """
        Convert a list of CommandDTO to a list of ICommand.

        Args:
            cmd_dto_list: The CommandDTO objects to convert.

        Returns:
            List: A list of ICommand instances.

        Raises:
            NotImplementedError: If the argument type is not implemented.
        """
        return [cmd for dto in cmd_dto_list for cmd in self.to_command(dto)]
