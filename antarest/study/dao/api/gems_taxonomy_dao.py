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

from antarest.study.business.model.gems.taxonomy import GemsTaxonomy


class ReadOnlyGemsTaxonomyDao(ABC):
    @abstractmethod
    def get_taxonomy(self) -> GemsTaxonomy | None:
        raise NotImplementedError()


class GemsTaxonomyDao(ReadOnlyGemsTaxonomyDao):
    @abstractmethod
    def save_taxonomy(self, taxonomy: GemsTaxonomy) -> None:
        """
        This method can only be used to add a taxonomy to a study, not to replace it.
        """
        raise NotImplementedError()
