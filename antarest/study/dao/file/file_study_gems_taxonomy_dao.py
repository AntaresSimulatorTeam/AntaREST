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

from antarest.study.business.model.gems.taxonomy import GemsTaxonomy
from antarest.study.dao.api.gems_taxonomy_dao import GemsTaxonomyDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader, YAMLWriter


def _get_gems_taxonomy_file_path(study_path: Path) -> Path:
    return study_path / "input" / "taxonomy.yml"


class FileStudyGemsTaxonomyDao(GemsTaxonomyDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_taxonomy(self) -> GemsTaxonomy | None:
        file_study = self.get_file_study()
        taxonomy_file_path = _get_gems_taxonomy_file_path(file_study.config.study_path)
        if not taxonomy_file_path.exists():
            return None

        yaml_content = YAMLReader().read(taxonomy_file_path)["taxonomy"]
        return GemsTaxonomy.model_validate(yaml_content)

    @override
    def save_taxonomy(self, taxonomy: GemsTaxonomy) -> None:
        taxonomy_file_path = _get_gems_taxonomy_file_path(self.get_file_study().config.study_path)
        yaml_content = taxonomy.model_dump(mode="json", exclude_unset=True, by_alias=True)
        YAMLWriter().write({"taxonomy": yaml_content}, taxonomy_file_path)
