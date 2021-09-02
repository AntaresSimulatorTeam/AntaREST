from typing import List

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
        self.generator_matrix_constants: GeneratorMatrixConstants = (
            generator_matrix_constants
        )
        self.matrix_service = matrix_service

    def to_icommand(self, command_dto: CommandDTO) -> List[ICommand]:
        if command_dto.action == CommandName.CREATE_AREA.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    CreateArea(
                        area_name=args["area_name"],
                        metadata=args["metadata"],
                        command_context=CommandContext(
                            generator_matrix_constants=self.generator_matrix_constants
                        ),
                    )
                ]

            elif isinstance(args := command_dto.args, list):
                return [
                    CreateArea(
                        area_name=arguments["area_name"],
                        metadata=arguments["metadata"],
                        command_context=CommandContext(
                            generator_matrix_constants=self.generator_matrix_constants
                        ),
                    )
                    for arguments in args
                ]
        elif command_dto.action == CommandName.UPDATE_AREA.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    UpdateArea(
                        id=args["id"],
                        name=args["name"],
                        metadata=args["metadata"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    UpdateArea(
                        id=arguments["id"],
                        name=arguments["name"],
                        metadata=arguments["metadata"],
                    )
                    for arguments in args
                ]
        elif command_dto.action == CommandName.REMOVE_AREA.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveArea(
                        id=args["id"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    RemoveArea(
                        id=arguments["id"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.CREATE_DISTRICT.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    CreateDistrict(
                        id=args["id"],
                        metadata=args["metadata"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    CreateDistrict(
                        id=arguments["id"],
                        metadata=arguments["metadata"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.UPDATE_DISTRICT.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    UpdateDistrict(
                        id=args["id"],
                        name=args["name"],
                        metadata=args["metadata"],
                        set=args["set"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    UpdateDistrict(
                        id=arguments["id"],
                        name=arguments["name"],
                        metadata=arguments["metadata"],
                        set=arguments["set"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.REMOVE_DISTRICT.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveDistrict(
                        id=args["id"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    RemoveDistrict(
                        id=arguments["id"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.CREATE_LINK.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    CreateLink(
                        area1=args["area1"],
                        area2=args["area2"],
                        parameters=args["parameters"],
                        series=args["series"],
                        command_context=CommandContext(
                            matrix_service=self.matrix_service
                        ),
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    CreateLink(
                        area1=arguments["area1"],
                        area2=arguments["area2"],
                        parameters=arguments["parameters"],
                        series=arguments["series"],
                        command_context=CommandContext(
                            matrix_service=self.matrix_service
                        ),
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.UPDATE_LINK.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    UpdateLink(
                        id=args["id"],
                        name=args["name"],
                        parameters=args["parameters"],
                        series=args["series"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    UpdateLink(
                        id=arguments["id"],
                        name=arguments["name"],
                        parameters=arguments["parameters"],
                        series=arguments["series"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.REMOVE_LINK.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveLink(
                        area1=args["area1"],
                        area2=args["area2"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    RemoveLink(
                        area1=arguments["area1"],
                        area2=arguments["area2"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.CREATE_BINDING_CONSTRAINT.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    CreateBindingConstraint(
                        name=args["name"],
                        enabled=args["enabled"],
                        time_step=args["time_step"],
                        operator=args["operator"],
                        coeffs=args["coeffs"],
                        values=args["values"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    CreateBindingConstraint(
                        name=arguments["name"],
                        enabled=arguments["enabled"],
                        time_step=arguments["time_step"],
                        operator=arguments["operator"],
                        coeffs=arguments["coeffs"],
                        values=arguments["values"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.UPDATE_BINDING_CONSTRAINT.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    UpdateBindingConstraint(
                        id=args["id"],
                        name=args["name"],
                        enabled=args["enabled"],
                        time_step=args["time_step"],
                        operator=args["operator"],
                        coeffs=args["coeffs"],
                        values=args["values"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    UpdateBindingConstraint(
                        id=arguments["id"],
                        name=arguments["name"],
                        enabled=arguments["enabled"],
                        time_step=arguments["time_step"],
                        operator=arguments["operator"],
                        coeffs=arguments["coeffs"],
                        values=arguments["values"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.REMOVE_BINDING_CONSTRAINT.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveBindingConstraint(
                        id=args["id"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    RemoveBindingConstraint(
                        id=arguments["id"],
                    )
                    for arguments in args
                ]
        elif command_dto.action == CommandName.CREATE_CLUSTER.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    CreateCluster(
                        name=args["name"],
                        type=args["type"],
                        parameters=args["parameters"],
                        prepro=args["prepro"],
                        modulation=args["modulation"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    CreateCluster(
                        name=arguments["name"],
                        type=arguments["type"],
                        parameters=arguments["parameters"],
                        prepro=arguments["prepro"],
                        modulation=arguments["modulation"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.UPDATE_CLUSTER.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    UpdateCluster(
                        id=args["id"],
                        name=args["name"],
                        type=args["type"],
                        parameters=args["parameters"],
                        prepro=args["prepro"],
                        modulation=args["modulation"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    UpdateCluster(
                        id=arguments["id"],
                        name=arguments["name"],
                        type=arguments["type"],
                        parameters=arguments["parameters"],
                        prepro=arguments["prepro"],
                        modulation=arguments["modulation"],
                    )
                    for arguments in args
                ]

        elif command_dto.action == CommandName.REMOVE_CLUSTER.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveCluster(
                        id=args["id"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    RemoveCluster(
                        id=arguments["id"],
                    )
                    for arguments in args
                ]
        elif command_dto.action == CommandName.REPLACE_MATRIX.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    ReplaceMatrix(
                        target_element=args["target_element"],
                        matrix=args["matrix"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    ReplaceMatrix(
                        target_element=arguments["target_element"],
                        matrix=arguments["matrix"],
                    )
                    for arguments in args
                ]
        elif command_dto.action == CommandName.UPDATE_CONFIG.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    UpdateConfig(
                        target=args["target"],
                        data=args["data"],
                    )
                ]
            elif isinstance(args := command_dto.args, list):
                return [
                    UpdateConfig(
                        target=arguments["target"],
                        data=arguments["data"],
                    )
                    for arguments in args
                ]
        raise NotImplementedError()
