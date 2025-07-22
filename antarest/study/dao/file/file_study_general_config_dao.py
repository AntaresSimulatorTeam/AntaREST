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
from abc import ABC, abstractmethod

from typing_extensions import override

from antarest.study.business.model.config.general_model import (
    GeneralConfig,
)
from antarest.study.dao.api.general_config_dao import GeneralConfigDao
from antarest.study.storage.rawstudy.model.filesystem.config.general import (
    parse_general_config,
    serialize_output_config,
    serialize_simulation_config,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyGeneralConfigDao(GeneralConfigDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_general_config(self) -> GeneralConfig:
        file_study = self.get_file_study()

        tree_data = file_study.tree.get(["settings", "generaldata"])

        return parse_general_config(tree_data)

    @override
    def save_general_config(self, config: GeneralConfig) -> None:
        study_data = self.get_file_study()

        current_config = study_data.tree.get(["settings", "generaldata"])
        current_general_config = current_config["general"]
        current_output_config = current_config["output"]

        general_config = serialize_simulation_config(config, study_data.config.version)
        general_config.update({k: v for k, v in current_general_config.items() if k not in general_config})

        general_output = serialize_output_config(config, study_data.config.version)
        general_output.update({k: v for k, v in current_output_config.items() if k not in general_output})

        current_config["general"] = general_config
        current_config["output"] = general_output

        study_data.tree.save(current_config, ["settings", "generaldata"])
