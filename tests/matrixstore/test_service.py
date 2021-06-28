import datetime
from unittest.mock import Mock, ANY

from antarest.matrixstore.model import (
    MatrixDTO,
    MatrixFreq,
    Matrix,
    MatrixContent,
)
from antarest.matrixstore.service import MatrixService


def test_save():
    # Init Mock
    repo_content = Mock()
    repo_content.save.return_value = "my-id"

    repo = Mock()

    # Input
    dto = MatrixDTO(
        freq=MatrixFreq.WEEKLY,
        created_at=42,
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    # Expected
    matrix = Matrix(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=ANY,
    )

    content = MatrixContent(
        index=["1", "2"], columns=["a", "b"], data=[[1, 2]]
    )

    # Test
    service = MatrixService(
        repo=repo, repo_meta=Mock(), content=repo_content, user_service=Mock()
    )
    id = service.create(dto)

    # Verify
    assert id == "my-id"
    repo.save.assert_called_once_with(matrix)
    repo_content.save.assert_called_once_with(content)


def test_get():
    # Init Mock
    content = Mock()
    content.get.return_value = MatrixContent(
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    repo = Mock()
    repo.get.return_value = Matrix(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=datetime.datetime.fromtimestamp(42),
    )

    repo_meta = Mock()

    # Expected
    exp = MatrixDTO(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=42,
        updated_at=101,
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    # Test
    service = MatrixService(repo, repo_meta, content, Mock())
    res = service.get("my-id")
    assert exp == res


def test_get_by_type_freq():
    content = Mock()
    content.get.return_value = MatrixContent(
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    repo = Mock()
    repo.get_by_freq.return_value = [
        Matrix(
            id="my-id",
            freq=MatrixFreq.WEEKLY,
            created_at=datetime.datetime.fromtimestamp(42),
        )
    ]

    repo_meta = Mock()

    # Expected
    exp = MatrixDTO(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=42,
        updated_at=101,
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    # Test
    service = MatrixService(repo, repo_meta, content, Mock())
    res = service.get_by_freq(freq=MatrixFreq.WEEKLY)
    assert [exp] == res
    repo.get_by_freq.assert_called_once_with(MatrixFreq.WEEKLY)


def test_delete():
    content = Mock()
    repo = Mock()
    repo_meta = Mock()

    service = MatrixService(repo, repo_meta, content, Mock())
    service.delete("my-id")
    content.delete.assert_called_once_with("my-id")
    repo.delete.assert_called_once_with("my-id")
