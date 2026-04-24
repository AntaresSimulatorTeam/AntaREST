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
from collections.abc import Sequence

import polars as pl

from antarest.study.business.model.link_model import Link
from antarest.study.dao.common import LinkSeriesMapping


class ReadOnlyLinkDao(ABC):
    @abstractmethod
    def get_links(self) -> Sequence[Link]:
        raise NotImplementedError()

    @abstractmethod
    def get_link(self, area1_id: str, area2_id: str) -> Link:
        raise NotImplementedError()

    @abstractmethod
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_link_indirect_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_link_direct_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_link_series(self, area_from: str, area_to: str) -> pl.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_all_links_series(self) -> LinkSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_links_indirect_capacities(self) -> LinkSeriesMapping:
        raise NotImplementedError()

    @abstractmethod
    def get_all_links_direct_capacities(self) -> LinkSeriesMapping:
        raise NotImplementedError()


class LinkDao(ReadOnlyLinkDao):
    @abstractmethod
    def save_links(self, links: Sequence[Link]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_link_indirect_capacities(self, series: LinkSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_link_direct_capacities(self, series: LinkSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_link_series(self, series: LinkSeriesMapping) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_link(self, link: Link) -> None:
        raise NotImplementedError()
