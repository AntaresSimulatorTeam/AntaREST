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


from antarest.study.business.model.gems.data_series import GemsDataSeries
from antarest.study.dao.api.gems_data_series import GemsDataSeriesDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase


class DatabaseGemsDataSeriesyDao(GemsDataSeriesDao, DatabaseDaoBase):
    def save_data_series(self, data_series: list[GemsDataSeries]) -> None:
        pass

    def get_data_series(self) -> list[GemsDataSeries]:
        return []
