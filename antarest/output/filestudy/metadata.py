# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import io
from pathlib import Path

from antarest.core.model import JSON
from antarest.core.serde.ini_common import DUPLICATE_KEYS
from antarest.core.serde.ini_reader import IniReader
from antarest.core.utils.archives import read_original_file_in_archive
from antarest.output.storage.output_storage import OutputDetails, OutputStorageType
from antarest.study.business.model.config.general_model import Mode


def parse_output_config(output_path: Path) -> JSON:
    if output_path.suffix == ".zip":
        # We need to read data from the archive
        content = read_original_file_in_archive(output_path, "about-the-study/parameters.ini")
        return IniReader(DUPLICATE_KEYS).read(io.StringIO(content.decode("utf-8")))
    return IniReader(DUPLICATE_KEYS).read(output_path / "about-the-study" / "parameters.ini")


def extract_output_details(output_path: Path) -> OutputDetails:
    # TODO: add some basic checks
    parameters_path = output_path / "about-the-study" / "parameters.ini"
    ini_reader = IniReader(special_keys=DUPLICATE_KEYS)
    parameters_dict = ini_reader.read(parameters_path)
    general = parameters_dict["general"]
    output = parameters_dict["output"]
    mode = Mode(general["mode"])
    return OutputDetails(
        id=output_path.name,
        name=output_path.name,  # TODO: should it be re-built from data instead ?
        mode=mode,
        synthesis=output["synthesis"],
        by_year=general["year-by-year"],
        nb_years=general["nbyears"],
        archived=False,
        storage_type=OutputStorageType.IN_STUDY_FILE_TREE,
    )
