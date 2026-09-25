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

from antarest.core.exceptions import GemsCatalogAlreadyExists
from antarest.study.business.model.gems.catalog import GemsCatalog
from antarest.study.dao.api.gems_catalog_dao import GemsCatalogDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader, YAMLWriter


def _get_gems_catalogs_folder_path(study_path: Path) -> Path:
    return study_path / "input" / "catalogs"


class FileStudyGemsCatalogDao(GemsCatalogDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_catalogs(self) -> list[GemsCatalog]:
        study = self.get_file_study()
        folder = _get_gems_catalogs_folder_path(study.config.study_path)
        if not folder.exists():
            return []

        catalogs: dict[str, GemsCatalog] = {}
        for path in sorted(folder.iterdir()):
            if not path.is_file() or path.suffix.lower() not in {".yml", ".yaml"}:
                continue
            catalog = GemsCatalog.model_validate(YAMLReader().read(path)["catalog"])
            if catalog.id in catalogs:
                raise GemsCatalogAlreadyExists(
                    f"Catalog '{catalog.id}' already exists for study {study.config.study_id}"
                )
            catalogs[catalog.id] = catalog
        return [catalogs[catalog_id] for catalog_id in sorted(catalogs)]

    @override
    def save_catalog(self, catalog: GemsCatalog) -> None:
        study = self.get_file_study()
        if any(existing.id == catalog.id for existing in self.get_catalogs()):
            raise GemsCatalogAlreadyExists(f"Catalog '{catalog.id}' already exists for study {study.config.study_id}")

        folder = _get_gems_catalogs_folder_path(study.config.study_path)
        path = folder / f"{catalog.id}.yaml"
        if path.exists():
            raise GemsCatalogAlreadyExists(
                f"Catalog file '{path.name}' already exists for study {study.config.study_id}"
            )

        folder.mkdir(parents=True, exist_ok=True)
        content = catalog.model_dump(mode="json", exclude_unset=True, by_alias=True)
        YAMLWriter().write({"catalog": content}, path)
