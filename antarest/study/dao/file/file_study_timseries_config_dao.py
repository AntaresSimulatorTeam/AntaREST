# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration
from antarest.study.dao.api.timeseries_config_dao import TimeSeriesConfigDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyTimeSeriesConfigDao(TimeSeriesConfigDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_timeseries_config(self) -> TimeSeriesConfiguration:
        file_study = self.get_file_study()
        nb_ts_gen_thermal = file_study.tree.get(["settings", "generaldata", "general", "nbtimeseriesthermal"])
        return TimeSeriesConfiguration.model_validate({"thermal": {"number": nb_ts_gen_thermal}})

    @override
    def save_timeseries_config(self, config: TimeSeriesConfiguration) -> None:
        file_study = self.get_file_study()
        file_study.tree.save(config.thermal.number, ["settings", "generaldata", "general", "nbtimeseriesthermal"])
