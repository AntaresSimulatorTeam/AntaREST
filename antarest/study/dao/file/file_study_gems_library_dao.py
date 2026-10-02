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

from antarest.core.exceptions import GemsLibraryAlreadyExists
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.dao.api.gems_library_dao import GemsLibraryDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader, YAMLWriter


def _get_gems_library_folder_path(study_path: Path) -> Path:
    return study_path / "input" / "model-libraries"


class FileStudyGemsLibraryDao(GemsLibraryDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_library(self) -> GemsLibrary | None:
        file_study = self.get_file_study()
        library_folder_path = _get_gems_library_folder_path(file_study.config.study_path)
        if not library_folder_path.exists() or not list(library_folder_path.iterdir()):
            return None

        all_library_files = list(library_folder_path.iterdir())
        if len(all_library_files) > 1:
            raise ValueError(f"Found more than one gems library file for study {file_study.config.study_id}")

        library_file = all_library_files[0]
        yaml_content = YAMLReader().read(library_file)["library"]
        return GemsLibrary.model_validate(yaml_content)

    @override
    def save_library(self, library: GemsLibrary) -> None:
        file_study = self.get_file_study()

        library_folder_path = _get_gems_library_folder_path(file_study.config.study_path)
        if library_folder_path.exists() and len(list(library_folder_path.iterdir())) > 0:
            raise GemsLibraryAlreadyExists(f"A library already exists for study {file_study.config.study_id}")

        yaml_content = library.model_dump(mode="json", exclude_unset=True, by_alias=True)
        library_folder_path.mkdir(exist_ok=True)
        YAMLWriter().write({"library": yaml_content}, library_folder_path / "library.yaml")
