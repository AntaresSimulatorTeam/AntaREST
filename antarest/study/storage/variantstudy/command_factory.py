from typing import List

from antarest.core.custom_types import JSON
from antarest.matrixstore.service import MatrixService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model import (
    CommandDTO,
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
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.update_area import (
    UpdateArea,
)
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import (
    UpdateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.update_cluster import (
    UpdateCluster,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command.update_district import (
    UpdateDistrict,
)
from antarest.study.storage.variantstudy.model.command.update_link import (
    UpdateLink,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class CommandFactory:
    """
    Service to convert CommendDTO to Command
    """

    def __init__(
        self,
        generator_matrix_constants: GeneratorMatrixConstants,
        matrix_service: MatrixService,
    ):
        self.command_context = CommandContext(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=matrix_service,
        )

    def _to_single_icommand(self, action: str, args: JSON) -> ICommand:
        assert isinstance(args, dict)
        if action == CommandName.CREATE_AREA.value:
            return CreateArea(
                area_name=args["area_name"],
                metadata=args["metadata"],
                command_context=self.command_context,
            )

        elif action == CommandName.UPDATE_AREA.value:
            return UpdateArea(
                id=args["id"],
                name=args["name"],
                metadata=args["metadata"],
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_AREA.value:
            return RemoveArea(
                id=args["id"],
                command_context=self.command_context,
            )

        elif action == CommandName.CREATE_DISTRICT.value:
            return CreateDistrict(
                id=args["id"],
                metadata=args["metadata"],
                command_context=self.command_context,
            )

        elif action == CommandName.UPDATE_DISTRICT.value:
            return UpdateDistrict(
                id=args["id"],
                name=args["name"],
                metadata=args["metadata"],
                set=args["set"],
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_DISTRICT.value:
            return RemoveDistrict(
                id=args["id"],
                command_context=self.command_context,
            )

        elif action == CommandName.CREATE_LINK.value:
            return CreateLink(
                area1=args["area1"],
                area2=args["area2"],
                parameters=args["parameters"],
                series=args.get("series", None),
                command_context=self.command_context,
            )

        elif action == CommandName.UPDATE_LINK.value:
            return UpdateLink(
                id=args["id"],
                name=args["name"],
                parameters=args["parameters"],
                series=args["series"],
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_LINK.value:
            return RemoveLink(
                area1=args["area1"],
                area2=args["area2"],
                command_context=self.command_context,
            )

        elif action == CommandName.CREATE_BINDING_CONSTRAINT.value:
            return CreateBindingConstraint(
                name=args["name"],
                enabled=args["enabled"],
                time_step=args["time_step"],
                operator=args["operator"],
                coeffs=args["coeffs"],
                values=args["values"],
                command_context=self.command_context,
            )

        elif action == CommandName.UPDATE_BINDING_CONSTRAINT.value:
            return UpdateBindingConstraint(
                id=args["id"],
                name=args["name"],
                enabled=args["enabled"],
                time_step=args["time_step"],
                operator=args["operator"],
                coeffs=args["coeffs"],
                values=args["values"],
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_BINDING_CONSTRAINT.value:
            return RemoveBindingConstraint(
                id=args["id"],
                command_context=self.command_context,
            )

        elif action == CommandName.CREATE_CLUSTER.value:
            return CreateCluster(
                area_name=args["area_name"],
                cluster_name=args["cluster_name"],
                parameters=args["parameters"],
                prepro=args.get("prepro", None),
                modulation=args.get("modulation", None),
                command_context=self.command_context,
            )

        elif action == CommandName.UPDATE_CLUSTER.value:
            return UpdateCluster(
                id=args["id"],
                name=args["name"],
                type=args["type"],
                parameters=args["parameters"],
                prepro=args["prepro"],
                modulation=args["modulation"],
                command_context=self.command_context,
            )

        elif action == CommandName.REMOVE_CLUSTER.value:
            return RemoveCluster(
                area_name=args["area_name"],
                cluster_name=args["cluster_name"],
                command_context=self.command_context,
            )

        elif action == CommandName.REPLACE_MATRIX.value:
            return ReplaceMatrix(
                target_element=args["target_element"],
                matrix=args["matrix"],
                command_context=self.command_context,
            )

        elif action == CommandName.UPDATE_CONFIG.value:
            return UpdateConfig(
                target=args["target"],
                data=args["data"],
                command_context=self.command_context,
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
