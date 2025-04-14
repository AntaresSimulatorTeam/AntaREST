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
from typing import Sequence

from antarest.study.business.model.link_model import LinkDTO


class ReadOnlyLinkDao(ABC):
    @abstractmethod
    def get_links(self) -> Sequence[LinkDTO]:
        raise NotImplementedError()

    @abstractmethod
    def get_link(self, area1_id: str, area2_id: str) -> LinkDTO:
        raise NotImplementedError()

    @abstractmethod
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        raise NotImplementedError()


class LinkDao(ReadOnlyLinkDao):
    @abstractmethod
    def save_link(self, area1_id: str, area2_id: str, link: LinkDTO) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_link_series(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError()
