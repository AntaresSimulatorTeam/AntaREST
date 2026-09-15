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
from unittest.mock import Mock

import pytest

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import STUDY_VERSION_10_2
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants


@pytest.fixture
def filestudy_dao_v10_2(empty_study_930: FileStudy, matrix_service: ISimpleMatrixService) -> FileStudyTreeDao:
    empty_study_930.config.version = STUDY_VERSION_10_2
    constants = GeneratorMatrixConstants(matrix_service)
    constants.init_constant_matrices()
    return FileStudyTreeDao(
        empty_study_930,
        False,
        constants,
        InMemoryBlobService(),
        matrix_service,
        Mock(),
    )
