from typing import Dict, Union, List, Any

from pydantic import validator

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.utils import (
    validate_matrix,
)


class CreateCluster(ICommand):
    area_name: str
    cluster_name: str
    parameters: Dict[str, str]
    prepro: Union[List[List[float]], str]
    modulation: Union[List[List[float]], str]
    # TODO: Maybe add the prefix option ?

    @validator("parameters")
    def check_parameters(cls, v: Dict[str, str]) -> Dict[str, str]:
        for parameter in [
            "group",
            "unitcount",
            "nominalcapacity",
            "marginal-cost",
            "market-bid-cost",
        ]:
            if parameter not in v.keys():
                raise ValueError(
                    f"Parameter '{parameter}' missing from parameters"
                )
        return v

    _validate_matrix = validator(
        "prepro", "modulation", each_item=True, always=True, allow_reuse=True
    )(validate_matrix)

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_CLUSTER, version=1, **data
        )

    def apply(self, study_data: FileStudy) -> CommandOutput:
        if self.area_name not in study_data.config.areas:
            return CommandOutput(
                status=False,
                message=f"Area '{self.area_name}' does not exist",
            )

        for cluster in study_data.config.areas[self.area_name].thermals:
            if cluster.id == self.cluster_name.lower():
                return CommandOutput(
                    status=False,
                    message=f"Cluster '{self.cluster_name}' already exist",
                )

        study_data.config.areas[self.area_name].thermals.append(
            Cluster(id=self.cluster_name.lower(), name=self.cluster_name)
        )

        self.parameters["name"] = self.cluster_name
        new_cluster_data: JSON = {
            "input": {
                "thermal": {
                    "clusters": {
                        self.area_name: {
                            "list": {self.cluster_name: self.parameters}
                        }
                    },
                    "prepro": {
                        self.area_name: {
                            self.cluster_name.lower(): {
                                "data": self.prepro,
                                "modulation": self.modulation,
                            }
                        }
                    },
                }
            }
        }
        study_data.tree.save(new_cluster_data)

        return CommandOutput(
            status=True,
            message=f"Cluster '{self.cluster_name}' added to area '{self.area_name}'",
        )

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
