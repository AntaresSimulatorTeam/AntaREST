from typing import List

from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model import (
    CommandDTO,
    ICommand,
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

    def __init__(self, generator_matrix_constants: GeneratorMatrixConstants):
        self.generator_matrix_constants: GeneratorMatrixConstants = (
            generator_matrix_constants
        )

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

            else:
                return [
                    CreateArea(
                        area_name=args["area_name"],
                        metadata=args["metadata"],
                        command_context=CommandContext(
                            generator_matrix_constants=self.generator_matrix_constants
                        ),
                    )
                    for args in command_dto.args
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
            else:
                return [
                    UpdateArea(
                        id=args["id"],
                        name=args["name"],
                        metadata=args["metadata"],
                    )
                    for args in command_dto.args
                ]
        elif command_dto.action == CommandName.REMOVE_AREA.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveArea(
                        id=args["id"],
                    )
                ]
            else:
                return [
                    RemoveArea(
                        id=args["id"],
                    )
                    for args in command_dto.args
                ]

        elif command_dto.action == CommandName.CREATE_DISTRICT.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    CreateDistrict(
                        id=args["id"],
                        metadata=args["metadata"],
                    )
                ]
            else:
                return [
                    CreateDistrict(
                        id=args["id"],
                        metadata=args["metadata"],
                    )
                    for args in command_dto.args
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
            else:
                return [
                    UpdateDistrict(
                        id=args["id"],
                        name=args["name"],
                        metadata=args["metadata"],
                        set=args["set"],
                    )
                    for args in command_dto.args
                ]

        elif command_dto.action == CommandName.REMOVE_DISTRICT.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveDistrict(
                        id=args["id"],
                    )
                ]
            else:
                return [
                    RemoveDistrict(
                        id=args["id"],
                    )
                    for args in command_dto.args
                ]

        elif command_dto.action == CommandName.CREATE_LINK.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    CreateLink(
                        name=args["name"],
                        parameters=args["parameters"],
                        series=args["series"],
                    )
                ]
            else:
                return [
                    CreateLink(
                        name=args["name"],
                        parameters=args["parameters"],
                        series=args["series"],
                    )
                    for args in command_dto.args
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
            else:
                return [
                    UpdateLink(
                        id=args["id"],
                        name=args["name"],
                        parameters=args["parameters"],
                        series=args["series"],
                    )
                    for args in command_dto.args
                ]

        elif command_dto.action == CommandName.REMOVE_LINK.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveLink(
                        id=args["id"],
                    )
                ]
            else:
                return [
                    RemoveLink(
                        id=args["id"],
                    )
                    for args in command_dto.args
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
            else:
                return [
                    CreateBindingConstraint(
                        name=args["name"],
                        enabled=args["enabled"],
                        time_step=args["time_step"],
                        operator=args["operator"],
                        coeffs=args["coeffs"],
                        values=args["values"],
                    )
                    for args in command_dto.args
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
            else:
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
                    for args in command_dto.args
                ]

        elif command_dto.action == CommandName.REMOVE_BINDING_CONSTRAINT.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveBindingConstraint(
                        id=args["id"],
                    )
                ]
            else:
                return [
                    RemoveBindingConstraint(
                        id=args["id"],
                    )
                    for args in command_dto.args
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
            else:
                return [
                    CreateCluster(
                        name=args["name"],
                        type=args["type"],
                        parameters=args["parameters"],
                        prepro=args["prepro"],
                        modulation=args["modulation"],
                    )
                    for args in command_dto.args
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
            else:
                return [
                    UpdateCluster(
                        id=args["id"],
                        name=args["name"],
                        type=args["type"],
                        parameters=args["parameters"],
                        prepro=args["prepro"],
                        modulation=args["modulation"],
                    )
                    for args in command_dto.args
                ]

        elif command_dto.action == CommandName.REMOVE_CLUSTER.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    RemoveCluster(
                        id=args["id"],
                    )
                ]
            else:
                return [
                    RemoveCluster(
                        id=args["id"],
                    )
                    for args in command_dto.args
                ]
        elif command_dto.action == CommandName.REPLACE_MATRIX.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    ReplaceMatrix(
                        target_element=args["target_element"],
                        matrix=args["matrix"],
                    )
                ]
            else:
                return [
                    ReplaceMatrix(
                        target_element=args["target_element"],
                        matrix=args["matrix"],
                    )
                    for args in command_dto.args
                ]
        elif command_dto.action == CommandName.UPDATE_CONFIG.value:
            if isinstance(args := command_dto.args, dict):
                return [
                    UpdateConfig(
                        target=args["target"],
                        data=args["data"],
                    )
                ]
            else:
                return [
                    UpdateConfig(
                        target=args["target"],
                        data=args["data"],
                    )
                    for args in command_dto.args
                ]
        else:
            raise NotImplementedError()
