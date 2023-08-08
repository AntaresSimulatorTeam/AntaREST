from typing import Any, List, Tuple, Dict

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils_binding_constraint import (
    remove_area_cluster_from_binding_constraints,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveRenewablesCluster(ICommand):
    area_id: str
    cluster_id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_RENEWABLES_CLUSTER,
            version=1,
            **data,
        )

    def _remove_renewables_cluster(
        self, study_data_config: FileStudyTreeConfig
    ) -> None:
        study_data_config.areas[self.area_id].renewables = [
            cluster
            for cluster in study_data_config.areas[self.area_id].renewables
            if cluster.id != self.cluster_id.lower()
        ]

        remove_area_cluster_from_binding_constraints(
            study_data_config, self.area_id, self.cluster_id
        )

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.area_id not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"Area '{self.area_id}' does not exist",
                ),
                {},
            )

        if not [
            cluster
            for cluster in study_data.areas[self.area_id].renewables
            if cluster.id == self.cluster_id
        ]:
            return (
                CommandOutput(
                    status=False,
                    message=f"Renewables cluster '{self.cluster_id}' does not exist",
                ),
                {},
            )
        self._remove_renewables_cluster(study_data)

        return (
            CommandOutput(
                status=True,
                message=f"Renewables cluster '{self.cluster_id}' removed from area '{self.area_id}'",
            ),
            {},
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        if self.area_id not in study_data.config.areas:
            return CommandOutput(
                status=False,
                message=f"Area '{self.area_id}' does not exist",
            )

        if not [
            cluster
            for cluster in study_data.config.areas[self.area_id].renewables
            if cluster.id == self.cluster_id
        ]:
            return CommandOutput(
                status=False,
                message=f"Renewables cluster '{self.cluster_id}' does not exist",
            )

        if len(study_data.config.areas[self.area_id].renewables) == 1:
            study_data.tree.delete(
                [
                    "input",
                    "renewables",
                ]
            )
        else:
            study_data.tree.delete(
                [
                    "input",
                    "renewables",
                    "clusters",
                    self.area_id,
                    "list",
                    self.cluster_id,
                ]
            )
            study_data.tree.delete(
                [
                    "input",
                    "renewables",
                    "series",
                    self.area_id,
                    self.cluster_id,
                ]
            )

        self._remove_renewables_cluster(study_data.config)

        return CommandOutput(
            status=True,
            message=f"Renewables cluster '{self.cluster_id}' removed from area '{self.area_id}'",
        )

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_RENEWABLES_CLUSTER.value,
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
        if not isinstance(other, RemoveRenewablesCluster):
            return False
        return (
            self.cluster_id == other.cluster_id
            and self.area_id == other.area_id
        )

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
