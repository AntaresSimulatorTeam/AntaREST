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
from pathlib import Path

import pytest
from antares.study.version.create_app import CreateApp

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.blobstore.service import IBlobService
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory, NormalizedMatrixUriMapper
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import STUDY_VERSION_9_3
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants


@pytest.fixture
def matrix_service() -> ISimpleMatrixService:
    return InMemorySimpleMatrixService()


@pytest.fixture
def blob_service() -> IBlobService:
    return InMemoryBlobService()


@pytest.fixture
def file_study(tmp_path: Path, matrix_service: ISimpleMatrixService) -> FileStudy:
    study_id = "5c22caca-b100-47e7-bbea-8b1b97aa26d9"
    study_path = tmp_path.joinpath(study_id)
    app = CreateApp(study_dir=study_path, caption="filestudy", version=STUDY_VERSION_9_3, author="Joe")
    app()
    config = build(study_path, study_id)
    mapper_factory = MatrixUriMapperFactory(matrix_service=matrix_service)
    matrix_mapper = mapper_factory.create(NormalizedMatrixUriMapper.NORMALIZED)
    return FileStudy(config, FileStudyTree(matrix_mapper, config))


@pytest.fixture
def filestudy_dao(file_study: FileStudy, matrix_service, blob_service) -> FileStudyTreeDao:
    constants = GeneratorMatrixConstants(matrix_service)
    constants.init_constant_matrices()
    return FileStudyTreeDao(file_study, False, constants, blob_service, matrix_service)
