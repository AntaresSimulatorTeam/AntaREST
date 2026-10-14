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
from typing import Any

import numpy as np
from typing_extensions import override

from antarest.core.serde.np_array import NpArray
from antarest.study.business.model.gems.data_series import GemsDataSeries
from antarest.study.dao.api.gems_data_series import GemsDataSeriesDao
from antarest.study.storage.rawstudy.model.filesystem.csv_file_node import CsvReader, CsvWriter
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def _get_gems_data_series_folder_path(study_path: Path) -> Path:
    return study_path / "input" / "data-series"


def _get_gems_data_series_files_path(study_path: Path) -> list[Path]:
    data_series_folder = _get_gems_data_series_folder_path(study_path)
    if not data_series_folder.exists():
        return []
    return list(data_series_folder.iterdir())


def _convert_csv_to_array(csv_content: Any) -> NpArray:
    csv_content_as_list = list(csv_content)
    csv_with_floats = [[float(s) for s in row] for row in csv_content_as_list]
    return np.array(csv_with_floats)


def _delete_old_data_series(data_series: list[GemsDataSeries], file_study: FileStudy):
    # Full replace: remove any previously saved data series omitted from this batch,
    # so a smaller/different batch doesn't leave stale files behind.

    new_ids = {ds.id for ds in data_series}
    for existing_file in _get_gems_data_series_files_path(file_study.config.study_path):
        if existing_file.name.split(".")[0] not in new_ids:
            existing_file.unlink()


def _write_new_data_series(data_series: list[GemsDataSeries], folder: Path):
    folder.mkdir(exist_ok=True)
    for ds in data_series:
        csv_content = ds.model_dump(mode="csv", exclude_unset=True)
        ds_path = folder / f"{ds.id}.csv"
        CsvWriter.write_rows(csv_content["values"], ds_path)


class FileStudyGemsDataSeriesDao(GemsDataSeriesDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_data_series(self) -> list[GemsDataSeries]:
        file_study = self.get_file_study()
        all_data_series_files = _get_gems_data_series_files_path(file_study.config.study_path)

        data_series_list = []
        for data_series_file in all_data_series_files:
            csv_content = CsvReader().read(data_series_file)
            ds_id = data_series_file.name.split(".")[0]
            current_ds = GemsDataSeries.model_validate({"id": ds_id, "values": _convert_csv_to_array(csv_content)})
            data_series_list.append(current_ds)

        return data_series_list

    @override
    def save_data_series(self, data_series: list[GemsDataSeries]) -> None:
        file_study = self.get_file_study()
        folder = _get_gems_data_series_folder_path(file_study.config.study_path)

        _delete_old_data_series(data_series, file_study)

        if not data_series:
            return

        _write_new_data_series(data_series, folder)
