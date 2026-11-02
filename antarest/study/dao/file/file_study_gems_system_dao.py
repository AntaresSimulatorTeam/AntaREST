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
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError
from typing_extensions import override

from antarest.core.exceptions import (
    GemsSystemAlreadyExists,
    GemsSystemIncorrectlyFormatted,
    GemsUnavailableForFileSystemStudies,
)
from antarest.core.serde.np_array import NpArray
from antarest.study.business.model.gems.system import GemsComponent, GemsSystem
from antarest.study.dao.api.gems_system_dao import GemsSystemDao
from antarest.study.storage.rawstudy.model.filesystem.csv_file_node import CsvReader, CsvWriter
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader, YAMLWriter

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def _get_gems_system_file_path(study_path: Path) -> Path:
    return study_path / "input" / "system.yml"


def _get_data_series_folder(study_path: Path) -> Path:
    return study_path / "input" / "data-series"


def _is_dependent(parameter: Any) -> bool:
    return bool(parameter.time_dependent or parameter.scenario_dependent)


class FileStudyGemsSystemyDao(GemsSystemDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_system(self) -> GemsSystem | None:
        file_study = self.get_file_study()
        system_file_path = _get_gems_system_file_path(file_study.config.study_path)
        if not system_file_path.exists():
            return None

        yaml_content = YAMLReader().read(system_file_path)["system"]
        try:
            system = GemsSystem.model_validate(yaml_content)
        except ValidationError as e:
            raise GemsSystemIncorrectlyFormatted(
                f"The system file of study {file_study.config.study_id} is not supported: {e}"
            ) from e

        self._save_data_series_to_matrix_store(system, file_study)
        return system

    def _save_data_series_to_matrix_store(self, system: GemsSystem, file_study: FileStudy) -> None:
        """
        Replaces, in place, the name of the data series files referenced by the time/scenario dependent
        parameters with the id of the matrix created from their content.
        """
        data_series_folder = _get_data_series_folder(file_study.config.study_path)
        dependent_parameters = [p for c in system.components for p in c.parameters if _is_dependent(p)]

        dataframes = []
        for parameter in dependent_parameters:
            file_path = data_series_folder / f"{parameter.value}.csv"
            if not file_path.is_file():
                raise GemsSystemIncorrectlyFormatted(
                    f"The system file of study {file_study.config.study_id} references a missing data series file: "
                    f"{file_path}"
                )
            dataframes.append(CsvReader.read(file_path))

        if dataframes:
            matrix_ids = self.get_impl().matrix_service.create_batch(iter(dataframes))
            for parameter, matrix_id in zip(dependent_parameters, matrix_ids):
                parameter.value = matrix_id

    @override
    def get_components(self) -> list[GemsComponent]:
        raise GemsUnavailableForFileSystemStudies(self.get_file_study().config.study_id)

    @override
    def get_parameter_value(self, component_id: str, parameter_id: str) -> NpArray:
        raise GemsUnavailableForFileSystemStudies(self.get_file_study().config.study_id)

    @override
    def save_system(self, system: GemsSystem) -> None:
        file_study = self.get_file_study()
        system_file_path = _get_gems_system_file_path(file_study.config.study_path)

        if system_file_path.exists():
            raise GemsSystemAlreadyExists(f"A system file already exists for study {file_study.config.study_id}")

        # Work on a copy, as the matrix ids are replaced by the names of the written data series files
        system = system.model_copy(deep=True)
        self._write_data_series_from_matrix_store(system, file_study)

        yaml_content = system.model_dump(mode="json", exclude_unset=True, by_alias=True)
        YAMLWriter().write({"system": yaml_content}, system_file_path)

    @override
    def save_components(self, components: list[GemsComponent]) -> None:
        raise GemsUnavailableForFileSystemStudies(self.get_file_study().config.study_id)

    def _write_data_series_from_matrix_store(self, system: GemsSystem, file_study: FileStudy) -> None:
        """
        Writes the content of the matrices referenced by the time/scenario dependent parameters as CSV files,
        and replaces, in place, the matrix ids with the names of the written files. The original names
        are not known, so they are built from the component and parameter ids.
        """
        matrix_service = self.get_impl().matrix_service
        data_series_folder = _get_data_series_folder(file_study.config.study_path)

        for component in system.components:
            for parameter in component.parameters:
                if not _is_dependent(parameter):
                    continue
                data_series_folder.mkdir(parents=True, exist_ok=True)
                name = f"{component.id}_{parameter.id}"
                CsvWriter.write(matrix_service.get(str(parameter.value)), data_series_folder / f"{name}.csv")
                parameter.value = name
