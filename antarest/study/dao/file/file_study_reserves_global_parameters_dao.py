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

from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.dao.api.reserves_global_parameters_dao import ReservesGlobalParametersDao
from antarest.study.dao.common import ReservesGlobalParametersMapping
from antarest.study.dao.file.common import check_area_exists
from antarest.study.storage.rawstudy.model.filesystem.config.reserves_global_parameters import (
    parse_reserves_global_parameters,
    serialize_reserves_global_parameters,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def _get_reserves_ini_path(area_id: str) -> list[str]:
    return ["input", "reserves", area_id, "reserves"]


class FileStudyReservesGlobalParametersDao(ReservesGlobalParametersDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_reserves_global_parameters(self, area_id: str) -> ReservesGlobalParameters:
        file_study = self.get_file_study()
        try:
            data = file_study.tree.get(_get_reserves_ini_path(area_id))
        except (ChildNotFoundError, KeyError):
            data = {}
        return parse_reserves_global_parameters(data)

    @override
    def get_all_reserves_global_parameters(self) -> ReservesGlobalParametersMapping:
        file_study = self.get_file_study()
        return {area_id: self.get_reserves_global_parameters(area_id) for area_id in file_study.config.areas}

    @override
    def save_reserves_global_parameters(self, mapping: ReservesGlobalParametersMapping) -> None:
        file_study = self.get_file_study()
        for area_id in mapping:
            check_area_exists(file_study.config, area_id)
        for area_id, params in mapping.items():
            path = _get_reserves_ini_path(area_id)
            try:
                existing_data = file_study.tree.get(path)
            except (ChildNotFoundError, KeyError):
                existing_data = {}
            existing_data["globalparameters"] = serialize_reserves_global_parameters(params)
            file_study.tree.save(existing_data, path)
