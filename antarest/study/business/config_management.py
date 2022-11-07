from typing import Dict, List, Optional

from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import (
    Study,
)
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_playlist import (
    UpdatePlaylist,
)


class ConfigManager:
    def __init__(
        self,
        storage_service: StudyStorageService,
    ) -> None:
        self.storage_service = storage_service

    def get_playlist(self, study: Study) -> Optional[Dict[int, float]]:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        return FileStudyHelpers.get_playlist(file_study)

    def set_playlist(
        self,
        study: Study,
        playlist: Optional[List[int]],
        weights: Optional[Dict[int, int]],
        reverse: bool,
        active: bool,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = UpdatePlaylist(
            items=playlist,
            weights=weights,
            reverse=reverse,
            active=active,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
