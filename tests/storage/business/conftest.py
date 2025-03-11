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
from zipfile import ZipFile

import pytest

from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.business.area_management import AreaManager
from antarest.study.business.link_management import LinkManager
from antarest.study.business.study_interface import FileStudyInterface, StudyInterface
from antarest.study.business.xpansion_management import XpansionManager
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.storage.business.assets import ASSETS_DIR


@pytest.fixture
def matrix_service() -> ISimpleMatrixService:
    return InMemorySimpleMatrixService()


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


@pytest.fixture(name="empty_study")
def empty_study_fixture(tmp_path: Path, matrix_service: ISimpleMatrixService) -> FileStudy:
    """
    Fixture for preparing an empty study in the `tmp_path`
    based on the "empty_study_810.zip" asset.

    Args:
        tmp_path: The temporary path provided by pytest.

    Returns:
        An instance of the `FileStudy` class representing the empty study.
    """
    study_id = "5c22caca-b100-47e7-bbea-8b1b97aa26d9"
    study_path = tmp_path.joinpath(study_id)
    study_path.mkdir()
    with ZipFile(ASSETS_DIR / "empty_study_810.zip") as zip_output:
        zip_output.extractall(path=study_path)
    config = build(study_path, study_id)
    context = ContextServer(matrix_service, UriResolverService(matrix_service))
    return FileStudy(config, FileStudyTree(context, config))


@pytest.fixture
def study(empty_study: FileStudy) -> StudyInterface:
    return FileStudyInterface(empty_study)
