# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from antarest.study.model import StudySimResultDTO, StudySimSettingsDTO
from antarest.study.storage.rawstudy.model.filesystem.config.files import get_playlist
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers


def extract_metadata(file_path: str) -> StudySimResultDTO:
    file_metadata = FileStudyHelpers.get_config(study_data, output_data.get_file())
    settings = StudySimSettingsDTO(
        general=file_metadata["general"],
        input=file_metadata["input"],
        output=file_metadata["output"],
        optimization=file_metadata["optimization"],
        otherPreferences=file_metadata["other preferences"],
        advancedParameters=file_metadata["advanced parameters"],
        seedsMersenneTwister=file_metadata["seeds - Mersenne Twister"],
        playlist=[year for year in (get_playlist(file_metadata) or {}).keys()],
    )

    return StudySimResultDTO(
        name=output_data.get_file(),
        type=output_data.mode,
        settings=settings,
        completionDate="",
        status="",
        archived=output_data.archived,
    )
