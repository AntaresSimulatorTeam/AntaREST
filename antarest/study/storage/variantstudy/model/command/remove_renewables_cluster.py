from typing import Any, Dict, List, Tuple

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils_binding_constraint import (
    remove_area_cluster_from_binding_constraints,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    MATCH_SIGNATURE_SEPARATOR,
    ICommand,
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

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        """
        Applies configuration changes to the study data: remove the renewable clusters from the storages list.

        Args:
            study_data: The study data configuration.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
            On success, the dictionary is empty.
        """
        # Search the Area in the configuration
        if self.area_id not in study_data.areas:
            message = (
                f"Area '{self.area_id}' does not exist"
                f" in the study configuration."
            )
            return CommandOutput(status=False, message=message), {}
        area: Area = study_data.areas[self.area_id]

        # Search the Renewable cluster in the area
        renewable = next(
            iter(
                renewable
                for renewable in area.renewables
                if renewable.id == self.cluster_id
            ),
            None,
        )
        if renewable is None:
            message = (
                f"Renewable cluster '{self.cluster_id}' does not exist"
                f" in the area '{self.area_id}'."
            )
            return CommandOutput(status=False, message=message), {}

        for renewable in area.renewables:
            if renewable.id == self.cluster_id:
                break
        else:
            message = (
                f"Renewable cluster '{self.cluster_id}' does not exist"
                f" in the area '{self.area_id}'."
            )
            return CommandOutput(status=False, message=message), {}

        # Remove the Renewable cluster from the configuration
        area.renewables.remove(renewable)

        remove_area_cluster_from_binding_constraints(
            study_data, self.area_id, self.cluster_id
        )

        message = (
            f"Renewable cluster '{self.cluster_id}' removed"
            f" from the area '{self.area_id}'."
        )
        return CommandOutput(status=True, message=message), {}

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        """
        Applies the study data to update renewable cluster configurations and saves the changes:
        remove corresponding the configuration and remove the attached time series.

        Args:
            study_data: The study data to be applied.

        Returns:
            The output of the command execution.
        """
        # It is required to delete the files and folders that correspond to the renewable cluster
        # BEFORE updating the configuration, as we need the configuration to do so.
        # Specifically, deleting the time series uses the list of renewable clusters from the configuration.
        # fmt: off
        paths = [
            ["input", "renewables", "clusters", self.area_id, "list", self.cluster_id],
            ["input", "renewables", "series", self.area_id, self.cluster_id],
        ]
        area: Area = study_data.config.areas[self.area_id]
        if len(area.renewables) == 1:
            paths.append(["input", "renewables", "series", self.area_id])
        # fmt: on
        for path in paths:
            study_data.tree.delete(path)
        # Deleting the renewable cluster in the configuration must be done AFTER
        # deleting the files and folders.
        return self._apply_config(study_data.config)[0]

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
