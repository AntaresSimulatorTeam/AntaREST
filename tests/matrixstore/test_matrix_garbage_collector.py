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
from unittest.mock import Mock

import pytest

from antarest.matrixstore.matrix_garbage_collector import MatrixGarbageCollector
from antarest.matrixstore.service import MatrixService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.repository import VariantStudyRepository


@pytest.fixture
def matrix_garbage_collector(tmp_path: Path):
    """
    Fixture for creating a MatrixGarbageCollector object.
    """
    matrix_store = tmp_path / "matrix_store"
    matrix_store.mkdir()
    default_workspace = tmp_path / "default_workspace"
    default_workspace.mkdir()
    mock_workspace_config = Mock()
    mock_workspace_config.path = default_workspace

    mock_config = Mock()
    mock_config.storage.matrixstore = matrix_store
    mock_config.storage.workspaces = {"default": mock_workspace_config}
    mock_config.storage.matrix_gc_dry_run = False

    matrix_constant_generator = Mock(spec=GeneratorMatrixConstants)
    matrix_constant_generator.hashes = {"test": "constant_matrix"}
    command_factory = CommandFactory(
        generator_matrix_constants=matrix_constant_generator,
        matrix_service=Mock(spec=MatrixService),
    )
    study_service = Mock()
    study_service.storage_service.variant_study_service.command_factory = command_factory
    study_service.storage_service.variant_study_service.repository = VariantStudyRepository(cache_service=Mock())

    matrix_garbage_collector = MatrixGarbageCollector(
        config=mock_config,
        matrix_service=Mock(),
    )

    return matrix_garbage_collector


@pytest.mark.unit_test
def test_get_saved_matrices(
    matrix_garbage_collector: MatrixGarbageCollector,
):
    """
    Test that the get_all_saved_matrices function returns a list of all saved
    matrices.
    """
    matrix_name1 = "matrix_name1"
    matrix_name2 = "matrix_name2"
    (matrix_garbage_collector.saved_matrices_path / f"{matrix_name1}.txt").touch()
    (matrix_garbage_collector.saved_matrices_path / f"{matrix_name2}.txt").touch()

    # Get all saved matrices
    saved_matrices = matrix_garbage_collector._get_saved_matrices()
    assert saved_matrices == {matrix_name1, matrix_name2}


@pytest.mark.unit_test
def test_delete_unused_saved_matrices(
    matrix_garbage_collector: MatrixGarbageCollector,
):
    unused_matrices = {"matrix1", "matrix2"}
    matrix_garbage_collector.matrix_service.delete = Mock()
    matrix_garbage_collector._delete_unused_saved_matrices(unused_matrices)

    matrix_garbage_collector.matrix_service.delete.assert_any_call("matrix1")
    matrix_garbage_collector.matrix_service.delete.assert_any_call("matrix2")

    matrix_garbage_collector.dry_run = True
    matrix_garbage_collector.matrix_service.delete.reset_mock()
    matrix_garbage_collector._delete_unused_saved_matrices(unused_matrices)
    matrix_garbage_collector.matrix_service.delete.assert_not_called()


@pytest.mark.unit_test
def test_clean_matrices(matrix_garbage_collector: MatrixGarbageCollector):
    matrix_garbage_collector._get_saved_matrices = Mock(return_value={"matrix1", "matrix2"})
    matrix_garbage_collector.matrix_service.get_used_matrices = Mock(return_value={"matrix1"})
    matrix_garbage_collector._delete_unused_saved_matrices = Mock()

    matrix_garbage_collector._clean_matrices()

    matrix_garbage_collector._delete_unused_saved_matrices.assert_called_once_with(unused_matrices={"matrix2"})
