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
from typing import Sequence

from typing_extensions import override

from antarest.core.exceptions import (
    GemsSystemAlreadyExists,
    GemsSystemNotFound,
    GemsUnavailableForFileSystemStudies,
)
from antarest.study.business.model.gems.system import (
    GemsAreaConnection,
    GemsComponent,
    GemsSystem,
    GemsThermalCapacityConnection,
    check_legacy_connections,
)
from antarest.study.dao.api.gems_system_dao import GemsSystemDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader, YAMLWriter


def _get_gems_system_file_path(study_path: Path) -> Path:
    return study_path / "input" / "system.yml"


class FileStudyGemsSystemyDao(GemsSystemDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_system(self) -> GemsSystem | None:
        file_study = self.get_file_study()
        system_file_path = _get_gems_system_file_path(file_study.config.study_path)
        if not system_file_path.exists():
            return None

        yaml_content = YAMLReader().read(system_file_path)["system"]
        return GemsSystem.model_validate(yaml_content)

    @override
    def get_components(self) -> list[GemsComponent]:
        raise GemsUnavailableForFileSystemStudies(self.get_file_study().config.study_id)

    @override
    def save_system(self, system: GemsSystem) -> None:
        file_study = self.get_file_study()
        system_file_path = _get_gems_system_file_path(file_study.config.study_path)

        if system_file_path.exists():
            raise GemsSystemAlreadyExists(f"A system file already exists for study {file_study.config.study_id}")

        yaml_content = system.model_dump(mode="json", exclude_unset=True, by_alias=True)
        YAMLWriter().write({"system": yaml_content}, system_file_path)

    @override
    def save_components(self, components: list[GemsComponent]) -> None:
        raise GemsUnavailableForFileSystemStudies(self.get_file_study().config.study_id)

    @override
    def save_area_connections(self, connections: list[GemsAreaConnection]) -> None:
        self._save_legacy_connections("area-connections", connections)

    @override
    def save_thermal_capacity_connections(self, connections: list[GemsThermalCapacityConnection]) -> None:
        self._save_legacy_connections("thermal-capacity-connections", connections)

    def _save_legacy_connections(
        self, section: str, connections: Sequence[GemsAreaConnection | GemsThermalCapacityConnection]
    ) -> None:
        file_study = self.get_file_study()
        system_file_path = _get_gems_system_file_path(file_study.config.study_path)
        if not system_file_path.exists():
            raise GemsSystemNotFound(f"No system configuration found for study {file_study.config.study_id}")

        # Works on the raw YAML content to leave the rest of the file untouched
        content = YAMLReader().read(system_file_path)
        system = content["system"]
        component_ids = {component["id"] for component in system.get("components") or []}
        check_legacy_connections(section, connections, component_ids)

        if connections:
            system[section] = [connection.model_dump(mode="json", by_alias=True) for connection in connections]
        else:
            system.pop(section, None)
        YAMLWriter().write(content, system_file_path)
