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
    GeneralFileData,
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
        config_data = tree_data.get("general", {})
        config_data.update(tree_data.get("output", {}))

        file_data = GeneralFileData.model_validate(config_data)
        return file_data.to_model()

    @override
    def save_general_config(self, config: GeneralConfig) -> None:
        study_data = self.get_file_study()

        current_general_config = study_data.tree.get(["settings", "generaldata", "general"])
        general_config = serialize_simulation_config(config, study_data.config.version)
        general_config.update({k: v for k, v in current_general_config.items() if k not in general_config})
        study_data.tree.save(general_config, ["settings", "generaldata", "general"])

        current_output_config = study_data.tree.get(["settings", "generaldata", "output"])
        general_output = serialize_output_config(config, study_data.config.version)
        general_output.update({k: v for k, v in current_output_config.items() if k not in general_output})
        study_data.tree.save(general_output, ["settings", "generaldata", "output"])
