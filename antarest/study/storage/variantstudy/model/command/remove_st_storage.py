from typing import Any, Dict, List, Tuple

from pydantic import Field

from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

# minimum required version.
REQUIRED_VERSION = 860


class RemoveSTStorage(ICommand):
    """
    Command used to remove a short-terme storage from an area.
    """

    area_id: str = Field(description="Area ID", regex=r"[a-z0-9_(),& -]+")
    storage_id: str = Field(
        description="Short term storage ID",
        regex=r"[a-z0-9_(),& -]+",
    )

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_ST_STORAGE, version=1, **data
        )

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        """
        Applies configuration changes to the study data: remove the storage from the storages list.

        Args:
            study_data: The study data configuration.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
            On success, the dictionary is empty.
        """
        # Check if the study version is above the minimum required version.
        version = study_data.version
        if version < REQUIRED_VERSION:
            return (
                CommandOutput(
                    status=False,
                    message=(
                        f"Invalid study version {version},"
                        f" at least version {REQUIRED_VERSION} is required."
                    ),
                ),
                {},
            )

        # Search the Area in the configuration
        if self.area_id not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=(
                        f"Area '{self.area_id}' does not exist"
                        f" in the study configuration."
                    ),
                ),
                {},
            )
        area: Area = study_data.areas[self.area_id]

        # Search the Short term storage in the area
        for st_storage in area.st_storages:
            if st_storage.id == self.storage_id:
                break
        else:
            return (
                CommandOutput(
                    status=False,
                    message=(
                        f"Short term storage '{self.storage_id}' does not exist"
                        f" in the area '{self.area_id}'."
                    ),
                ),
                {},
            )

        # Remove the Short term storage from the configuration
        area.st_storages.remove(st_storage)

        return (
            CommandOutput(
                status=True,
                message=(
                    f"Short term storage '{self.storage_id}' removed"
                    f" from the area '{self.area_id}'."
                ),
            ),
            {},
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        """
        Applies the study data to update storage configurations and saves the changes:
        remove the storage from the configuration and remove the attached time series.

        Args:
            study_data: The study data to be applied.

        Returns:
            The output of the command execution.
        """
        # It is required to delete the files and folders that correspond to the short-term storage
        # BEFORE updating the configuration, as we need the configuration to do so.
        # Specifically, deleting the time series uses the list of short-term storages from the configuration.
        # fmt: off
        paths = [
            ["input", "st-storage", "clusters", self.area_id, "list", self.storage_id],
            ["input", "st-storage", "series", self.area_id, self.storage_id],
        ]
        area: Area = study_data.config.areas[self.area_id]
        if len(area.st_storages) == 1:
            paths.append(["input", "st-storage", "series", self.area_id])
        # fmt: on
        for path in paths:
            study_data.tree.delete(path)
        # Deleting the short-term storage in the configuration must be done AFTER
        # deleting the files and folders.
        return self._apply_config(study_data.config)[0]

    def to_dto(self) -> CommandDTO:
        """
        Converts the current object to a Data Transfer Object (DTO)
        which is stored in the `CommandBlock` in the database.

        Returns:
            The DTO object representing the current command.
        """
        return CommandDTO(
            action=self.command_name.value,
            args={"area_id": self.area_id, "storage_id": self.storage_id},
        )

    def match_signature(self) -> str:
        """Returns the command signature."""
        return str(
            self.command_name.value
            + MATCH_SIGNATURE_SEPARATOR
            + self.area_id
            + MATCH_SIGNATURE_SEPARATOR
            + self.storage_id
        )

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        # always perform a deep comparison, as there are no parameters
        # or matrices, so that shallow and deep comparisons are identical.
        return self.__eq__(other)

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
