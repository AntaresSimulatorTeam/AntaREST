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
from typing import Any, Callable

from typing_extensions import override

from antarest.core.exceptions import GemsSystemAlreadyExists, GemsUnavailableForFileSystemStudies
from antarest.study.business.model.gems.system import GemsComponent, GemsSystem
from antarest.study.dao.api.gems_system_dao import GemsSystemDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader, YAMLWriter


def _get_gems_system_file_path(study_path: Path) -> Path:
    return study_path / "input" / "system.yml"


def _remove_legacy_connections(
    study_path: Path,
    is_area_connection_removed: Callable[[dict[str, Any]], bool],
    is_thermal_capacity_connection_removed: Callable[[dict[str, Any]], bool],
) -> None:
    """
    Removes connections from the system file, working on the raw YAML content to leave the rest of the file untouched.
    """
    system_file_path = _get_gems_system_file_path(study_path)
    if not system_file_path.exists():
        return

    content = YAMLReader().read(system_file_path)
    system = content["system"]
    has_changed = False
    for section, is_removed in [
        ("area-connections", is_area_connection_removed),
        ("thermal-capacity-connections", is_thermal_capacity_connection_removed),
    ]:
        connections = system.get(section) or []
        kept_connections = [connection for connection in connections if not is_removed(connection)]
        if len(kept_connections) != len(connections):
            has_changed = True
            if kept_connections:
                system[section] = kept_connections
            else:
                del system[section]

    if has_changed:
        YAMLWriter().write(content, system_file_path)


def _thermal_component(connection: dict[str, Any]) -> tuple[str, str]:
    thermal_component = connection.get("thermal-component") or {}
    return str(thermal_component.get("area", "")).lower(), str(thermal_component.get("cluster-id", "")).lower()


def remove_area_from_gems_system(study_path: Path, area_id: str) -> None:
    """
    Removes the connections of the GEMS system to a deleted legacy area and to its thermal clusters.
    The components stay in the system.
    """
    area_id = area_id.lower()
    _remove_legacy_connections(
        study_path,
        lambda connection: str(connection.get("area", "")).lower() == area_id,
        lambda connection: _thermal_component(connection)[0] == area_id,
    )


def remove_thermal_cluster_from_gems_system(study_path: Path, area_id: str, cluster_id: str) -> None:
    """
    Removes the connections of the GEMS system to a deleted legacy thermal cluster.
    The components stay in the system.
    """
    thermal_component = (area_id.lower(), cluster_id.lower())
    _remove_legacy_connections(
        study_path,
        lambda connection: False,
        lambda connection: _thermal_component(connection) == thermal_component,
    )


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
