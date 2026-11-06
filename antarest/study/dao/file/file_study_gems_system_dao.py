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
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from polars import DataFrame
from pydantic import ValidationError
from typing_extensions import override

from antarest.core.exceptions import (
    GemsSystemAlreadyExists,
    GemsSystemIncorrectlyFormatted,
    GemsUnavailableForFileSystemStudies,
)
from antarest.core.utils.polars import read_csv
from antarest.study.business.model.gems.system import GemsComponent, GemsSystem
from antarest.study.dao.api.gems_system_dao import GemsSystemDao
from antarest.study.storage.rawstudy.model.filesystem.csv_file_node import CsvWriter
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader, YAMLWriter

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def _get_gems_system_file_path(study_path: Path) -> Path:
    return study_path / "input" / "system.yml"


def _get_data_series_folder(study_path: Path) -> Path:
    return study_path / "input" / "data-series"


# Only plain names are accepted: no path separator, no dot (hence no `..`, no extension), no drive letter.
_DATA_SERIES_NAME_PATTERN = re.compile(r"[\w\-]+", re.ASCII)


def _resolve_data_series_file(data_series_folder: Path, name: str, study_id: str) -> Path:
    """
    Resolves the name of a data series to its CSV file, guaranteeing that the file is a regular
    file located directly inside `data_series_folder`.
    """
    if not _DATA_SERIES_NAME_PATTERN.fullmatch(name):
        raise GemsSystemIncorrectlyFormatted(
            f"The system file of study {study_id} references an invalid data series name: {name!r}. "
            f"Only letters, digits, '_' and '-' are allowed."
        )

    file_path = data_series_folder / f"{name}.csv"

    if not file_path.is_file():
        raise GemsSystemIncorrectlyFormatted(
            f"The system file of study {study_id} references a missing data series file: {name!r}"
        )
    return file_path


class FileStudyGemsSystemDao(GemsSystemDao, ABC):
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

        # Matrices are stored in the matrix store to ensure compatibility with the database implementation.
        # As this will only be called in the converter, this is not a performance issue.
        self._save_data_series_to_matrix_store(system, file_study)
        return system

    def _save_data_series_to_matrix_store(self, system: GemsSystem, file_study: FileStudy) -> None:
        """
        Replaces, in place, the name of the data series files referenced by the time/scenario dependent
        parameters with the id of the matrix created from their content.
        """
        data_series_folder = _get_data_series_folder(file_study.config.study_path)
        dependent_parameters = [p for c in system.components for p in c.parameters if p.is_dataseries()]

        dataframes = []
        for parameter in dependent_parameters:
            file_path = _resolve_data_series_file(
                data_series_folder, parameter.get_value_as_str(), file_study.config.study_id
            )
            dataframes.append(read_csv(file_path, has_headers=False))

        if dataframes:
            matrix_ids = self.get_impl().matrix_service.create_batch(iter(dataframes))
            for parameter, matrix_id in zip(dependent_parameters, matrix_ids):
                parameter.value = matrix_id

    @override
    def get_components(self) -> list[GemsComponent]:
        raise GemsUnavailableForFileSystemStudies(self.get_file_study().config.study_id)

    @override
    def get_parameter_series(self, component_id: str, parameter_id: str) -> DataFrame:
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

        mapping_matrix_id_to_csv = {}
        matrices_count = 0

        data_series_folder.mkdir(parents=True, exist_ok=True)
        for component in system.components:
            for parameter in component.parameters:
                if not parameter.is_dataseries():
                    continue

                str_value = parameter.get_value_as_str()
                # Update the parameter value with the name of the CSV file only if it has not been written yet
                if str_value not in mapping_matrix_id_to_csv:
                    name = f"data_series_{matrices_count}"
                    matrices_count += 1
                    CsvWriter.write(matrix_service.get(str_value), data_series_folder / f"{name}.csv")
                    mapping_matrix_id_to_csv[str_value] = name
                    parameter.value = name
                else:
                    parameter.value = mapping_matrix_id_to_csv[str_value]
