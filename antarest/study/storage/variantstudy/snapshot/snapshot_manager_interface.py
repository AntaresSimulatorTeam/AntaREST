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

from antarest.study.model import Study
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy


class ISnapshotManager(ABC):
    @abstractmethod
    def is_snapshot_up_to_date(self, study: VariantStudy) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def has_snapshot(self, study: VariantStudy) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def create_snapshot(self, ref_study: Study, variant_study: VariantStudy) -> None:
        raise NotImplementedError()

    @abstractmethod
    def clear_snapshot(self, variant_study: VariantStudy) -> None:
        raise NotImplementedError()
