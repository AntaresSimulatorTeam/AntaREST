from typing import Any

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveCluster(ICommand):
    area_id: str
    cluster_id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_CLUSTER, version=1, **data
        )

    def apply(self, study_data: FileStudy) -> CommandOutput:
        if self.area_id not in study_data.config.areas:
            return CommandOutput(
                status=False,
                message=f"Area '{self.area_id}' does not exist",
            )

        if (
            len(
                [
                    cluster
                    for cluster in study_data.config.areas[
                        self.area_id
                    ].thermals
                    if cluster.id == self.cluster_id
                ]
            )
            == 0
        ):
            return CommandOutput(
                status=False,
                message=f"Cluster '{self.cluster_id}' does not exist",
            )
        study_data.tree.delete(
            [
                "input",
                "thermal",
                "clusters",
                self.area_id,
                "list",
                self.cluster_id,
            ]
        )
        study_data.tree.delete(
            [
                "input",
                "thermal",
                "prepro",
                self.area_id,
                self.cluster_id,
            ]
        )
        study_data.tree.delete(
            [
                "input",
                "thermal",
                "series",
                self.area_id,
                self.cluster_id,
            ]
        )

        study_data.config.areas[self.area_id].thermals = [
            cluster
            for cluster in study_data.config.areas[self.area_id].thermals
            if cluster.id != self.cluster_id.lower()
        ]
        return CommandOutput(
            status=True,
            message=f"Cluster '{self.cluster_id}' removed from area '{self.area_id}'",
        )

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
