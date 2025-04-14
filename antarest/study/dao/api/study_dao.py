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
from abc import abstractmethod
from typing import Sequence

from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.study.business.model.link_model import LinkDTO
from antarest.study.dao.api.link_dao import LinkDao, ReadOnlyLinkDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class ReadOnlyStudyDao(ReadOnlyLinkDao):
    @abstractmethod
    def get_version(self) -> StudyVersion:
        raise NotImplementedError()


class StudyDao(ReadOnlyStudyDao, LinkDao):
    """
    Abstraction for access to study data. Handles all reading
    and writing from underlying storage format.
    """

    def read_only(self) -> ReadOnlyStudyDao:
        """
        Returns a read only version of this DAO,
        to ensure it's not used for writing.
        """
        return ReadOnlyAdapter(self)

    @abstractmethod
    def as_file_study(self) -> FileStudy:
        """
        To ease transition, to be removed when all goes through other methods
        """
        raise NotImplementedError()


class ReadOnlyAdapter(ReadOnlyStudyDao):
    """
    Adapts a full DAO as a read only DAO without modification methods.
    """

    def __init__(self, adaptee: StudyDao):
        self._adaptee = adaptee

    @override
    def get_version(self) -> StudyVersion:
        return self._adaptee.get_version()

    @override
    def get_links(self) -> Sequence[LinkDTO]:
        return self._adaptee.get_links()

    @override
    def get_link(self, area1_id: str, area2_id: str) -> LinkDTO:
        return self._adaptee.get_link(area1_id, area2_id)

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        return self._adaptee.link_exists(area1_id, area2_id)
