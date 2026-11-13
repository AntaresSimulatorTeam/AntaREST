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
from pathlib import Path

from typing_extensions import override

from antarest.study.business.model.gems.optim_config import GemsOptimConfig
from antarest.study.dao.api.gems_optim_config_dao import GemsOptimConfigDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader, YAMLWriter


def _get_gems_optim_config_file_path(study_path: Path) -> Path:
    return study_path / "input" / "optim-config.yml"


class FileStudyGemsOptimConfigDao(GemsOptimConfigDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_optim_config(self) -> GemsOptimConfig | None:
        file_study = self.get_file_study()
        file_path = _get_gems_optim_config_file_path(file_study.config.study_path)
        if not file_path.exists():
            return None
        yaml_content = YAMLReader().read(file_path) or {}
        return GemsOptimConfig.model_validate(yaml_content)

    @override
    def save_optim_config(self, optim_config: GemsOptimConfig) -> None:
        file_study = self.get_file_study()
        file_path = _get_gems_optim_config_file_path(file_study.config.study_path)
        yaml_content = optim_config.model_dump(mode="json", by_alias=True, exclude_none=True)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        YAMLWriter().write(yaml_content, file_path)
