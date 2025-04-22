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
from pathlib import Path

import pytest
from antares.study.version.create_app import CreateApp

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.business.area_management import AreaManager
from antarest.study.business.link_management import LinkManager
from antarest.study.business.study_interface import FileStudyInterface, StudyInterface
from antarest.study.business.xpansion_management import XpansionManager
from antarest.study.model import STUDY_VERSION_8_1
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.fixture
def command_context(matrix_service: ISimpleMatrixService) -> CommandContext:
    matrix_constants = GeneratorMatrixConstants(matrix_service)
    matrix_constants.init_constant_matrices()
    return CommandContext(generator_matrix_constants=matrix_constants, matrix_service=matrix_service)


@pytest.fixture
def xpansion_manager(command_context: CommandContext) -> XpansionManager:
    return XpansionManager(command_context)


@pytest.fixture
def area_manager(command_context: CommandContext) -> AreaManager:
    return AreaManager(command_context)


@pytest.fixture
def link_manager(command_context: CommandContext) -> LinkManager:
    return LinkManager(command_context)


@pytest.fixture
def study(tmp_path: Path, matrix_service: ISimpleMatrixService) -> StudyInterface:
    study_id = "5c22caca-b100-47e7-bbea-8b1b97aa26d9"
    study_path = tmp_path.joinpath(study_id)
    app = CreateApp(study_dir=study_path, caption="empty_study_810", version=STUDY_VERSION_8_1, author="Unknown")
    app()
    config = build(study_path, study_id)
    empty_study_810 = FileStudy(config, FileStudyTree(UriResolverService(matrix_service), config))
    return FileStudyInterface(empty_study_810)
