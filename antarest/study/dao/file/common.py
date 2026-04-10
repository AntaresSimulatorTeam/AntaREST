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
from antarest.core.exceptions import AreaNotFound
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig


def check_area_exists(study_data: FileStudyTreeConfig, area_id: str) -> None:
    if area_id not in study_data.areas:
        raise AreaNotFound(f"The area '{area_id}' does not exist")
