from typing import Any

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveCluster(ICommand):
    area_name: str
    cluster_name: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_CLUSTER, version=1, **data
        )

    def apply(self, study_data: FileStudy) -> CommandOutput:
        if self.area_name not in study_data.config.areas:
            return CommandOutput(
                status=False,
                message=f"Area '{self.area_name}' does not exist",
            )

        if (
            len(
                [
                    cluster
                    for cluster in study_data.config.areas[
                        self.area_name
                    ].thermals
                    if cluster.id == self.cluster_name.lower()
                ]
            )
            == 0
        ):
            return CommandOutput(
                status=False,
                message=f"Cluster '{self.cluster_name}' does not exist",
            )
        study_data.tree.delete(
            [
                "input",
                "thermal",
                "clusters",
                self.area_name,
                "list",
                self.cluster_name,
            ]
        )
        study_data.tree.delete(
            [
                "input",
                "thermal",
                "prepro",
                self.area_name,
                self.cluster_name.lower(),
            ]
        )

        study_data.config.areas[self.area_name].thermals = [
            cluster
            for cluster in study_data.config.areas[self.area_name].thermals
            if cluster.id != self.cluster_name.lower()
        ]
        return CommandOutput(
            status=True,
            message=f"Cluster '{self.cluster_name}' removed from area '{self.area_name}'",
        )

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
