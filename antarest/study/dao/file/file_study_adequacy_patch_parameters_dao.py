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

from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters
from antarest.study.dao.api.adequacy_patch_parameters_dao import AdequacyPatchParametersDao
from antarest.study.storage.rawstudy.model.filesystem.config.adequacy_patch_parameters import (
    parse_adequacy_patch_parameters,
    serialize_adequacy_patch_parameters,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

ADEQUACY_PATCH_PATH = ["settings", "generaldata", "adequacy patch"]


class FileStudyAdequacyPatchParametersDao(AdequacyPatchParametersDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_adequacy_patch_parameters(self) -> AdequacyPatchParameters:
        file_study = self.get_file_study()
        data = file_study.tree.get(ADEQUACY_PATCH_PATH)
        return parse_adequacy_patch_parameters(file_study.config.version, data)

    @override
    def save_adequacy_patch_parameters(self, parameters: AdequacyPatchParameters) -> None:
        file_study = self.get_file_study()
        data = file_study.tree.get(ADEQUACY_PATCH_PATH)
        new_content = serialize_adequacy_patch_parameters(file_study.config.version, parameters)

        # Include fields that are in the generaldata.ini file but not in the FileData class
        new_content.update({k: v for k, v in data.items() if k not in new_content})

        file_study.tree.save(new_content, ADEQUACY_PATCH_PATH)
