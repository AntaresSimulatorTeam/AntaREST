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

from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.study.dao.file.file_study_link_dao import FileStudyLinkDao
from antarest.study.dao.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyTreeDao(StudyDao, FileStudyLinkDao):
    """
    Implementation of study DAO over the simulator input format.
    """

    def __init__(self, study: FileStudy) -> None:
        self._file_study = study

    @override
    @property
    def impl(self) -> "FileStudyTreeDao":
        return self

    @override
    def as_file_study(self) -> FileStudy:
        """
        To ease transition, to be removed when all goes through other methods
        """
        return self._file_study

    @override
    def get_version(self) -> StudyVersion:
        return self._file_study.config.version
