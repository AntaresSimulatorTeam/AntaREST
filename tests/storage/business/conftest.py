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
import pytest

from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.area_management import AreaManager
from antarest.study.business.link_management import LinkManager
from antarest.study.business.xpansion_management import XpansionManager
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext


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
