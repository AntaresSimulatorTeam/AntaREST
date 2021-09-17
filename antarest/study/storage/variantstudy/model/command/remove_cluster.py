from typing import Any, List, Optional

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.command_group import (
    CommandGroup,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.variant_command_extractor import (
    VariantCommandsExtractor,
)


class RemoveCluster(ICommand):
    area_id: str
    cluster_id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_CLUSTER, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
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

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_CLUSTER.value,
            args={"area_id": self.area_id, "cluster_id": self.cluster_id},
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveCluster):
            return False
        return (
            self.cluster_id == other.cluster_id
            and self.area_id == other.area_id
        )

    def revert(self, history: List["ICommand"], base: FileStudy) -> "ICommand":
        for command in reversed(history):
            if (
                isinstance(command, CreateCluster)
                and transform_name_to_id(command.cluster_name)
                == self.cluster_id
                and command.area_id == self.area_id
            ):
                return command
        return CommandGroup(
            command_list=VariantCommandsExtractor(
                self.command_context.matrix_service
            ).extract_cluster(base, self.area_id, self.cluster_id),
            command_context=self.command_context,
        )
