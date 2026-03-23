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


from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyHelpers:
    @staticmethod
    def get_config(study: FileStudy, output_id: str | None = None) -> JSON:
        if output_id:
            config_path = [
                "output",
                output_id,
                "about-the-study",
                "parameters",
            ]
            config = study.tree.get(config_path)
            return config
        return study.tree.get(["settings", "generaldata"])
