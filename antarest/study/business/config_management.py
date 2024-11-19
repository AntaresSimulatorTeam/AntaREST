# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from typing import Dict, List, Optional

from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_playlist import UpdatePlaylist


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
            study_version=file_study.config.version,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)
