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
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

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

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def _get_general_parameters(file_study: FileStudy) -> dict[str, Any]:
    args = {}
    for keyword in ["general", "output"]:
        try:
            data = file_study.tree.get(["settings", "generaldata", keyword])
        except KeyError:
            data = {}
        args[keyword] = data
    return args


class FileStudyGeneralConfigDao(GeneralConfigDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_general_config(self) -> GeneralConfig:
        file_study = self.get_file_study()

        general_data = _get_general_parameters(file_study)

        return parse_general_config(general_data, file_study.config.version)

    @override
    def save_general_config(self, config: GeneralConfig) -> None:
        study_data = self.get_file_study()

        current_config = _get_general_parameters(study_data)
        current_general_config = current_config["general"]
        current_output_config = current_config["output"]

        general_config = serialize_simulation_config(config, study_data.config.version)
        general_config.update({k: v for k, v in current_general_config.items() if k not in general_config})

        general_output = serialize_output_config(config, study_data.config.version)
        general_output.update({k: v for k, v in current_output_config.items() if k not in general_output})

        study_data.tree.save(general_config, ["settings", "generaldata", "general"])
        study_data.tree.save(general_output, ["settings", "generaldata", "output"])
