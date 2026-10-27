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
from enum import StrEnum
from pathlib import Path

GEMS_VIEWS_DIR = "gems_views"


class OutputType(StrEnum):
    LEGACY = "LEGACY"
    GEMS_VIEWS = "GEMS_VIEWS"

    @staticmethod
    def from_output_dir(output_dir: Path) -> "OutputType":
        if (output_dir / GEMS_VIEWS_DIR).is_dir():
            return OutputType.GEMS_VIEWS  # implicit interface agreement with the Simulator
        return OutputType.LEGACY
