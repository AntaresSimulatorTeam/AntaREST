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
from pathlib import Path

from antarest.core.serde.ini_reader import IniReader
from antarest.study.model import StudySimResultDTO, StudySimSettingsDTO
from antarest.study.storage.rawstudy.model.filesystem.config.files import get_playlist

DUPLICATE_KEYS = [
    "playlist_year_weight",
    "playlist_year +",
    "playlist_year -",
    "select_var -",
    "select_var +",
]


def extract_metadata(output_path: Path) -> StudySimResultDTO:
    # TODO: add some basic checks
    parameters_path = output_path / "about-the-study" / "parameters.ini"
    ini_reader = IniReader(special_keys=DUPLICATE_KEYS)
    parameters_dict = ini_reader.read(parameters_path)

    settings = StudySimSettingsDTO(
        general=parameters_dict["general"],
        input=parameters_dict["input"],
        output=parameters_dict["output"],
        optimization=parameters_dict["optimization"],
        otherPreferences=parameters_dict["other preferences"],
        advancedParameters=parameters_dict["advanced parameters"],
        seedsMersenneTwister=parameters_dict["seeds - Mersenne Twister"],
        playlist=list((get_playlist(parameters_dict) or {}).keys()),
    )
    # TODO: maybe the short version "eco" is expected, instead of "Economy"
    #       is it anyway useful ??
    mode = parameters_dict["general"]["mode"]
    return StudySimResultDTO(
        name=output_path.name,
        type=mode,
        settings=settings,
        completionDate="",
        status="",
        archived=False,
    )
