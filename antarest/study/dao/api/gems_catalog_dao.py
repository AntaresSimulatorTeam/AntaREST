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

from antarest.study.business.model.gems.catalog import GemsCatalog


class ReadOnlyGemsCatalogDao(ABC):
    @abstractmethod
    def get_catalogs(self) -> list[GemsCatalog]:
        raise NotImplementedError()


class GemsCatalogDao(ReadOnlyGemsCatalogDao):
    @abstractmethod
    def save_catalogs(self, catalogs: list[GemsCatalog]) -> None:
        """
        Add catalogs to a study. Existing catalogs cannot be replaced.
        Reject duplicate identifiers within the batch or the study before writing any catalog.
        An empty batch does nothing.
        """
        raise NotImplementedError()
