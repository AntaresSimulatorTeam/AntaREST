from typing import Any, List, Tuple, Dict

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
    FileStudyTreeConfig,
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
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveCluster(ICommand):
    area_id: str
    cluster_id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_CLUSTER, version=1, **data
        )

    def _remove_constraints(self, study_data: FileStudyTreeConfig):
        study_data.areas[self.area_id].thermals = [
            cluster
            for cluster in study_data.areas[self.area_id].thermals
            if cluster.id != self.cluster_id.lower()
        ]

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.area_id not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"Area '{self.area_id}' does not exist",
                ),
                dict(),
            )

        if (
            len(
                [
                    cluster
                    for cluster in study_data.areas[self.area_id].thermals
                    if cluster.id == self.cluster_id
                ]
            )
            == 0
        ):
            return (
                CommandOutput(
                    status=False,
                    message=f"Cluster '{self.cluster_id}' does not exist",
                ),
                dict(),
            )
        self._remove_constraints(study_data)
        # todo remove binding constraint using this cluster ?

        return (
            CommandOutput(
                status=True,
                message=f"Cluster '{self.cluster_id}' removed from area '{self.area_id}'",
            ),
            dict(),
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

        self._remove_constraints(study_data.config)

        return CommandOutput(
            status=True,
            message=f"Cluster '{self.cluster_id}' removed from area '{self.area_id}'",
        )

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_CLUSTER.value,
            args={"area_id": self.area_id, "cluster_id": self.cluster_id},
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value
            + MATCH_SIGNATURE_SEPARATOR
            + self.cluster_id
            + MATCH_SIGNATURE_SEPARATOR
            + self.area_id
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveCluster):
            return False
        return (
            self.cluster_id == other.cluster_id
            and self.area_id == other.area_id
        )

    def revert(
        self, history: List["ICommand"], base: FileStudy
    ) -> List["ICommand"]:
        from antarest.study.storage.variantstudy.model.command.create_cluster import (
            CreateCluster,
        )
        from antarest.study.storage.variantstudy.model.command.utils_extractor import (
            CommandExtraction,
        )

        for command in reversed(history):
            if (
                isinstance(command, CreateCluster)
                and transform_name_to_id(command.cluster_name)
                == self.cluster_id
                and command.area_id == self.area_id
            ):
                # todo revert binding constraints that has the cluster in constraint and also search in base for one
                return [command]

        return (
            self.command_context.command_extractor
            or CommandExtraction(self.command_context.matrix_service)
        ).extract_cluster(base, self.area_id, self.cluster_id)
        # todo revert binding constraints that has the cluster in constraint

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
