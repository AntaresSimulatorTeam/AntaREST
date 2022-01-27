from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.matrixstore.matrix_garbage_collector import (
    MatrixGarbageCollector,
)
from antarest.study.service import StudyService


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

    matrix_garbage_collector = MatrixGarbageCollector(
        config=mock_config, study_service=Mock()
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
    (
        matrix_garbage_collector.saved_matrices_path / f"{matrix_name1}.txt"
    ).touch()
    (
        matrix_garbage_collector.saved_matrices_path / f"{matrix_name2}.txt"
    ).touch()

    # Get all saved matrices
    saved_matrices = matrix_garbage_collector._get_saved_matrices()
    assert saved_matrices == {matrix_name1, matrix_name2}


@pytest.mark.unit_test
def test_get_matrices_used_in_raw_studies():
    pass


@pytest.mark.unit_test
def test_get_matrices_used_in_variant_studies():
    pass


@pytest.mark.unit_test
def test_get_matrices_used_in_dataset():
    pass
