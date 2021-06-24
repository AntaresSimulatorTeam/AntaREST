from pathlib import Path
from typing import Optional, List
from unittest.mock import Mock

from antarest.matrixstore.service import MatrixService
from antarest.storage.business.uri_resolver_service import UriResolverService
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.matrix.matrix import MatrixNode


class MockMatrixNode(MatrixNode):
    def __init__(self, context: ContextServer, config: StudyConfig) -> None:
        super().__init__(
            config=config,
            context=context,
        )

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return "Mock Content Matrix"

    def dump(self, data: str, url: Optional[List[str]] = None) -> None:
        self.config.path.write_text(data)

    def build(self, config: StudyConfig) -> TREE:
        pass  # not used

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass  # not used


def test_save_managed_link(tmp_path: Path):
    file = tmp_path / "my-study/matrix.txt"
    file.parent.mkdir()
    file.touch()
    # (file.parent / "matrix.txt.link").touch()

    resolver = Mock()
    resolver.is_managed.return_value = True

    config = StudyConfig(study_path=file, study_id="my-study")

    node = MockMatrixNode(
        context=ContextServer(matrix=Mock(), resolver=resolver), config=config
    )

    node.save("matrix://my-id")
    resolver.is_managed.assert_called_once_with("my-study")
    assert not file.exists()
    assert (file.parent / "matrix.txt.link").read_text() == "matrix://my-id"


def test_save_managed_content(tmp_path: Path):
    file = tmp_path / "my-study/matrix.txt"
    file.parent.mkdir()
    file.touch()
    # (file.parent / "matrix.txt.link").touch()

    mock_matrix = {
        "index": ["1", "2"],
        "columns": ["a", "b"],
        "data": [[1, 2], [3, 4]],
    }

    resolver = Mock()
    resolver.is_managed.return_value = True
    resolver.build_matrix_uri.return_value = "matrix://my-id"

    matrix = Mock()
    matrix.create.return_value = "my-id"

    config = StudyConfig(study_path=file, study_id="my-study")

    node = MockMatrixNode(
        context=ContextServer(matrix=matrix, resolver=resolver), config=config
    )

    node.save(mock_matrix)
    resolver.is_managed.assert_called_once_with("my-study")
    matrix.create.assert_called_once_with(mock_matrix)
    assert not file.exists()
    assert (file.parent / "matrix.txt.link").read_text() == "matrix://my-id"
