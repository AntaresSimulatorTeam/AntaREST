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

from antarest.study.business.model.gems.data_series import GemsDataSeries


class ReadOnlyGemsDataSeriesDao(ABC):
    @abstractmethod
    def get_data_series(self) -> list[GemsDataSeries]:
        """Return the data series, or an empty list if no data series are configured."""
        raise NotImplementedError()


class GemsDataSeriesDao(ReadOnlyGemsDataSeriesDao):
    @abstractmethod
    def save_data_series(self, data_series: list[GemsDataSeries]) -> None:
        """Create or replace the complete data series, removing omitted groups. An empty data series clears it."""
        raise NotImplementedError()
