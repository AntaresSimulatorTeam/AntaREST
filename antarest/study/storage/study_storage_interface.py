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
from typing import BinaryIO

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import RawStudy, Study
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy


class IStudyStorage(ABC):
    @abstractmethod
    def get_dao(self, study: Study) -> StudyDao:
        raise NotImplementedError()

    @abstractmethod
    def copy(self, src_study: Study, new_study: RawStudy) -> RawStudy:
        raise NotImplementedError()

    @abstractmethod
    def write_study_to_filesytem(self, study: Study) -> None:
        raise NotImplementedError()

    @abstractmethod
    def write_study_for_archive(self, study: RawStudy) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_disk_usage(self, study: Study) -> int:
        raise NotImplementedError()

    @abstractmethod
    def normalize_study(self, study: Study) -> None:
        raise NotImplementedError()

    @abstractmethod
    def import_study(self, study: RawStudy, stream: BinaryIO) -> RawStudy:
        raise NotImplementedError()

    @abstractmethod
    def is_snapshot_up_to_date(self, study: VariantStudy) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def create_snapshot(self, ref_study: Study, variant_study: VariantStudy) -> None:
        raise NotImplementedError()

    @abstractmethod
    def clear_snapshot(self, variant_study: VariantStudy) -> None:
        raise NotImplementedError()
