from pathlib import Path
from typing import Optional, List
from unittest.mock import Mock

from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.matrix.lazy_matrix import (
    LazyMatrix,
)


class MockLazyMatrix(LazyMatrix[str, str, str]):
    def __init__(self, context: ContextServer, path: Path) -> None:
        super().__init__(
            context=context,
            config=StudyConfig(study_path=path),
            url_prefix="file",
        )

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return "Mock Matrix Content"

    def dump(self, data: str, url: Optional[List[str]] = None) -> None:
        self.config.path.write_text(data)

    def build(self, config: StudyConfig) -> TREE:
        pass  # not used

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass  # not used


def test_get_expanded_parsed(tmp_path: Path):
    file = tmp_path / "123456.link"
    file.touch()

    node = MockLazyMatrix(context=Mock(), path=file)
    assert node.get(expanded=True) == "123456"


def test_get_expanded_no_parsed(tmp_path: Path):
    file = tmp_path / "abc"
    file.touch()

    matrix_service = Mock()
    matrix_service.create.return_value = "123456"

    node = MockLazyMatrix(
        context=ContextServer(matrix=matrix_service), path=file
    )
    assert node.get(expanded=True) == "123456"
    matrix_service.create.assert_called_once_with("Mock Matrix Content")
    assert not file.exists()
    assert (tmp_path / "123456.link").exists()


def test_get_not_expanded_parsed(tmp_path: Path):
    file = tmp_path / "123456.link"
    file.touch()

    matrix_service = Mock()
    matrix_service.get.return_value = "Mock Matrix Content"

    node = MockLazyMatrix(
        context=ContextServer(matrix=matrix_service), path=file
    )
    assert node.get() == "Mock Matrix Content"
    matrix_service.get.assert_called_once_with("123456")


def test_get_not_expanded_not_parsed(tmp_path: Path):
    file = tmp_path / "abc"
    file.touch()

    matrix_service = Mock()
    matrix_service.create.return_value = "123456"

    node = MockLazyMatrix(
        context=ContextServer(matrix=matrix_service), path=file
    )

    assert node.get() == "Mock Matrix Content"
    matrix_service.create.assert_called_once_with("Mock Matrix Content")
    assert not file.exists()
    assert (tmp_path / "123456.link").exists()
