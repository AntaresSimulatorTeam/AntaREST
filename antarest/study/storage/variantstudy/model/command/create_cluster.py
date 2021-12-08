from typing import Dict, Union, List, Any, Optional, cast, Tuple

from pydantic import validator

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Cluster,
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.command.utils import (
    validate_matrix,
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateCluster(ICommand):
    area_id: str
    cluster_name: str
    parameters: Dict[str, str]
    prepro: Optional[Union[List[List[MatrixData]], str]] = None
    modulation: Optional[Union[List[List[MatrixData]], str]] = None
    # TODO: Maybe add the prefix option ?

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_CLUSTER, version=1, **data
        )

    @validator("cluster_name")
    def validate_cluster_name(cls, val: str) -> str:
        valid_name = transform_name_to_id(val, lower=False)
        if valid_name != val:
            raise ValueError(
                "Area name must only contains [a-zA-Z0-9],&,-,_,(,) characters"
            )
        return val

    @validator("prepro", always=True)
    def validate_prepro(
        cls, v: Optional[Union[List[List[MatrixData]], str]], values: Any
    ) -> Optional[Union[List[List[MatrixData]], str]]:
        if v is None:
            v = values[
                "command_context"
            ].generator_matrix_constants.get_thermal_prepro_data()
            return v

        else:
            return validate_matrix(v, values)

    @validator("modulation", always=True)
    def validate_modulation(
        cls, v: Optional[Union[List[List[MatrixData]], str]], values: Any
    ) -> Optional[Union[List[List[MatrixData]], str]]:
        if v is None:
            v = values[
                "command_context"
            ].generator_matrix_constants.get_thermal_prepro_modulation()
            return v

        else:
            return validate_matrix(v, values)

    def _apply_config(
        self, study_data: FileStudy
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.area_id not in study_data.config.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"Area '{self.area_id}' does not exist",
                ),
                dict(),
            )

        cluster_id = transform_name_to_id(self.cluster_name)
        for cluster in study_data.config.areas[self.area_id].thermals:
            if cluster.id == cluster_id:
                return (
                    CommandOutput(
                        status=False,
                        message=f"Cluster '{self.cluster_name}' already exist",
                    ),
                    dict(),
                )

        study_data.config.areas[self.area_id].thermals.append(
            Cluster(id=cluster_id, name=self.cluster_name)
        )
        return (
            CommandOutput(
                status=True,
                message=f"Cluster '{self.cluster_name}' added to area '{self.area_id}'",
            ),
            {"cluster_id": cluster_id},
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        output, data = self.apply_config(study_data)
        if not output.status:
            return output

        cluster_id = data["cluster_id"]

        cluster_list_config = study_data.tree.get(
            ["input", "thermal", "clusters", self.area_id, "list"]
        )
        cluster_list_config[self.cluster_name] = self.parameters

        self.parameters["name"] = self.cluster_name
        new_cluster_data: JSON = {
            "input": {
                "thermal": {
                    "clusters": {self.area_id: {"list": cluster_list_config}},
                    "prepro": {
                        self.area_id: {
                            cluster_id: {
                                "data": self.prepro,
                                "modulation": self.modulation,
                            }
                        }
                    },
                    "series": {
                        self.area_id: {
                            cluster_id: {
                                "series": self.command_context.generator_matrix_constants.get_null_matrix()
                            }
                        }
                    },
                }
            }
        }
        study_data.tree.save(new_cluster_data)

        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_CLUSTER.value,
            args={
                "area_id": self.area_id,
                "cluster_name": self.cluster_name,
                "parameters": self.parameters,
                "prepro": strip_matrix_protocol(self.prepro),
                "modulation": strip_matrix_protocol(self.modulation),
            },
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value
            + MATCH_SIGNATURE_SEPARATOR
            + self.area_id
            + MATCH_SIGNATURE_SEPARATOR
            + self.cluster_name
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, CreateCluster):
            return False
        simple_match = (
            self.area_id == other.area_id
            and self.cluster_name == other.cluster_name
        )
        if not equal:
            return simple_match
        return (
            simple_match
            and self.parameters == other.parameters
            and self.prepro == other.prepro
            and self.modulation == other.modulation
        )

    def revert(
        self, history: List["ICommand"], base: FileStudy
    ) -> List["ICommand"]:
        from antarest.study.storage.variantstudy.model.command.remove_cluster import (
            RemoveCluster,
        )

        cluster_id = transform_name_to_id(self.cluster_name)
        return [
            RemoveCluster(
                area_id=self.area_id,
                cluster_id=cluster_id,
                command_context=self.command_context,
            )
        ]

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        other = cast(CreateCluster, other)
        from antarest.study.storage.variantstudy.model.command.replace_matrix import (
            ReplaceMatrix,
        )
        from antarest.study.storage.variantstudy.model.command.update_config import (
            UpdateConfig,
        )

        cluster_id = transform_name_to_id(self.cluster_name)
        commands: List[ICommand] = []
        if self.prepro != other.prepro:
            commands.append(
                ReplaceMatrix(
                    target=f"input/thermal/prepro/{self.area_id}/{cluster_id}/data",
                    matrix=strip_matrix_protocol(other.prepro),
                    command_context=self.command_context,
                )
            )
        if self.modulation != other.modulation:
            commands.append(
                ReplaceMatrix(
                    target=f"input/thermal/prepro/{self.area_id}/{cluster_id}/modulation",
                    matrix=strip_matrix_protocol(other.modulation),
                    command_context=self.command_context,
                )
            )
        if self.parameters != other.parameters:
            commands.append(
                UpdateConfig(
                    target=f"input/thermal/clusters/{self.area_id}/list/{self.cluster_name}",
                    data=other.parameters,
                    command_context=self.command_context,
                )
            )
        return commands

    def get_inner_matrices(self) -> List[str]:
        matrices: List[str] = []
        if self.prepro:
            assert isinstance(self.prepro, str)
            matrices.append(strip_matrix_protocol(self.prepro))
        if self.modulation:
            assert isinstance(self.modulation, str)
            matrices.append(strip_matrix_protocol(self.modulation))
        return matrices
