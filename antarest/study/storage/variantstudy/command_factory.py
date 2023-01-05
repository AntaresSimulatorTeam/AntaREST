from typing import List

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import (
    CreateRenewablesCluster,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import (
    RemoveBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.remove_cluster import (
    RemoveCluster,
)
from antarest.study.storage.variantstudy.model.command.remove_district import (
    RemoveDistrict,
)
from antarest.study.storage.variantstudy.model.command.remove_link import (
    RemoveLink,
)
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import (
    RemoveRenewablesCluster,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import (
    UpdateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.update_comments import (
    UpdateComments,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command.update_district import (
    UpdateDistrict,
)
from antarest.study.storage.variantstudy.model.command.update_playlist import (
    UpdatePlaylist,
)
from antarest.study.storage.variantstudy.model.command.update_raw_file import (
    UpdateRawFile,
)
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
)


class CommandFactory:
    """
    Service to convert CommendDTO to Command
    """

    def __init__(
        self,
        generator_matrix_constants: GeneratorMatrixConstants,
        matrix_service: ISimpleMatrixService,
        patch_service: PatchService,
    ):
        self.command_context = CommandContext(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=matrix_service,
            patch_service=patch_service,
        )

    def _to_single_icommand(self, action: str, args: JSON) -> ICommand:
        assert_this(isinstance(args, dict))
        if action == CommandName.CREATE_AREA.value:
            return CreateArea(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_AREA.value:
            return RemoveArea(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.CREATE_DISTRICT.value:
            return CreateDistrict(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_DISTRICT.value:
            return RemoveDistrict(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.CREATE_LINK.value:
            return CreateLink(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_LINK.value:
            return RemoveLink(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.CREATE_BINDING_CONSTRAINT.value:
            return CreateBindingConstraint(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.UPDATE_BINDING_CONSTRAINT.value:
            return UpdateBindingConstraint(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_BINDING_CONSTRAINT.value:
            return RemoveBindingConstraint(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.CREATE_CLUSTER.value:
            return CreateCluster(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_CLUSTER.value:
            return RemoveCluster(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.CREATE_RENEWABLES_CLUSTER.value:
            return CreateRenewablesCluster(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_RENEWABLES_CLUSTER.value:
            return RemoveRenewablesCluster(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.REPLACE_MATRIX.value:
            return ReplaceMatrix(
                **args,
                command_context=self.command_context,
            )

        elif action == CommandName.UPDATE_CONFIG.value:
            return UpdateConfig(
                **args,
                command_context=self.command_context,
            )
        elif action == CommandName.UPDATE_COMMENTS.value:
            return UpdateComments(
                **args,
                command_context=self.command_context,
            )
        elif action == CommandName.UPDATE_FILE.value:
            return UpdateRawFile(
                **args,
                command_context=self.command_context,
            )
        elif action == CommandName.UPDATE_DISTRICT.value:
            return UpdateDistrict(
                **args,
                command_context=self.command_context,
            )
        elif action == CommandName.UPDATE_PLAYLIST.value:
            return UpdatePlaylist(
                **args,
                command_context=self.command_context,
            )
        elif action == CommandName.UPDATE_SCENARIO_BUILDER.value:
            return UpdateScenarioBuilder(
                **args,
                command_context=self.command_context
            )
        raise NotImplementedError()

    def to_icommand(self, command_dto: CommandDTO) -> List[ICommand]:
        args = command_dto.args
        if isinstance(args, dict):
            return [self._to_single_icommand(command_dto.action, args)]

        elif isinstance(args, list):
            output_list = []
            for argument in args:
                output_list.append(
                    self._to_single_icommand(command_dto.action, argument)
                )
            return output_list

        raise NotImplementedError()
