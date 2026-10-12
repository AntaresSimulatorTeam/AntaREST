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
import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
from typing_extensions import override

from antarest.core.serde.np_array import NpArray
from antarest.study.business.model.gems.data_series import GemsDataSeries
from antarest.study.dao.api.gems_data_series import GemsDataSeriesDao
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
    csv_with_floats = [[float(s)] for row in csv_content_as_list for s in row]
    return np.array(csv_with_floats)


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
            with open(data_series_file, "r") as f:
                csv_content = csv.reader(f)
                ds_id = data_series_file.name.split(".")[0]
                current_ds = GemsDataSeries.model_validate({"id": ds_id, "values": _convert_csv_to_array(csv_content)})
                data_series_list.append(current_ds)

        return data_series_list

    @override
    def save_data_series(self, data_series: list[GemsDataSeries]) -> None:
        file_study = self.get_file_study()

        for ds in data_series:
            csv_content = ds.model_dump(mode="csv", exclude_unset=True)
            _get_gems_data_series_folder_path(file_study.config.study_path).mkdir(exist_ok=True)
            ds_path = _get_gems_data_series_folder_path(file_study.config.study_path) / f"{ds.id}.csv"

            with open(ds_path, "w") as f:
                writer = csv.writer(f)
                writer.writerows(csv_content["values"])
