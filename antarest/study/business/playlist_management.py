from typing import Dict, Union, List

from pydantic.types import StrictBool, StrictFloat, StrictInt

from antarest.study.business.general_management import FIELDS_INFO
from antarest.study.business.utils import (
    FormFieldsBaseModel,
    execute_or_add_commands,
)
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_playlist import (
    UpdatePlaylist,
)

DEFAULT_WEIGHT = 1


class PlaylistColumns(FormFieldsBaseModel):
    status: StrictBool
    weight: Union[StrictFloat, StrictInt]


class PlaylistManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_table_data(
        self,
        study: RawStudy,
    ) -> Dict[int, PlaylistColumns]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        playlist = FileStudyHelpers.get_playlist(file_study) or {}
        nb_years = file_study.tree.get(
            FIELDS_INFO["nb_years"]["path"].split("/")
        ) or len(playlist)

        return {
            year: PlaylistColumns.construct(
                status=year in playlist,
                # TODO the real value for disable year
                weight=playlist.get(year, DEFAULT_WEIGHT),
            )
            for year in range(1, int(nb_years) + 1)  # type: ignore
        }

    def set_table_data(
        self,
        study: RawStudy,
        data: Dict[int, PlaylistColumns],
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        years_by_bool: Dict[bool, List[int]] = {True: [], False: []}
        for year, col in data.items():
            years_by_bool[col.status].append(year - 1)

        active_playlists = [
            year for year, col in data.items() if col.status is True
        ]

        weights = {
            year: col.weight
            for year, col in data.items()
            if col.weight != DEFAULT_WEIGHT
        }

        execute_or_add_commands(
            study,
            file_study,
            [
                UpdatePlaylist(
                    items=active_playlists,
                    weights=weights,
                    active=True,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            ],
            self.storage_service,
        )
