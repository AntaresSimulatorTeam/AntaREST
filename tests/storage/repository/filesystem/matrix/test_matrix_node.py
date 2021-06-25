import json
from pathlib import Path
from typing import Optional, List
from unittest.mock import Mock

from antarest.common.custom_types import JSON
from antarest.matrixstore.model import MatrixDTO, MatrixFreq
from antarest.matrixstore.service import MatrixService
from antarest.storage.business.uri_resolver_service import UriResolverService
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.matrix.matrix import MatrixNode


class MockMatrixNode(MatrixNode):
    def __init__(self, context: ContextServer, config: StudyConfig) -> None:
        super().__init__(config=config, context=context, freq="annual")

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return "Mock Content Matrix"

    def dump(self, data: JSON, url: Optional[List[str]] = None) -> None:
        json.dump(data, self.config.path.open("w"))

    def build(self, config: StudyConfig) -> TREE:
        pass  # not used

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass  # not used


MOCK_MATRIX_JSON = {
    "index": ["1", "2"],
    "columns": ["a", "b"],
    "data": [[1, 2], [3, 4]],
}

MOCK_MATRIX_DTO = MatrixDTO(
    freq=MatrixFreq.ANNUAL,
    index=["1", "2"],
    columns=["a", "b"],
    data=[[1, 2], [3, 4]],
)


def test_save_managed_uri(tmp_path: Path):
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

    resolver = Mock()
    resolver.is_managed.return_value = True
    resolver.build_matrix_uri.return_value = "matrix://my-id"

    matrix = Mock()
    matrix.create.return_value = "my-id"

    config = StudyConfig(study_path=file, study_id="my-study")

    node = MockMatrixNode(
        context=ContextServer(matrix=matrix, resolver=resolver), config=config
    )

    node.save(MOCK_MATRIX_JSON)
    resolver.is_managed.assert_called_once_with("my-study")
    matrix.create.assert_called_once_with(MOCK_MATRIX_DTO)
    assert not file.exists()
    assert (file.parent / "matrix.txt.link").read_text() == "matrix://my-id"


def test_save_no_managed_uri(tmp_path: Path):
    file = tmp_path / "my-study/matrix.txt"
    file.parent.mkdir()
    file.touch()
    # (file.parent / "matrix.txt.link").touch()

    resolver = Mock()
    resolver.is_managed.return_value = False
    resolver.resolve.return_value = MOCK_MATRIX_JSON

    matrix = Mock()
    matrix.get.return_value = MOCK_MATRIX_DTO

    config = StudyConfig(study_path=file, study_id="my-study")

    node = MockMatrixNode(
        context=ContextServer(matrix=matrix, resolver=resolver), config=config
    )

    node.save("matrix://my-id")
    resolver.is_managed.assert_called_once_with("my-study")
    assert file.read_text() == json.dumps(MOCK_MATRIX_JSON)


def test_save_no_managed_content(tmp_path: Path):
    file = tmp_path / "my-study/matrix.txt"
    file.parent.mkdir()

    resolver = Mock()
    resolver.is_managed.return_value = False

    config = StudyConfig(study_path=file, study_id="my-study")

    node = MockMatrixNode(
        context=ContextServer(matrix=Mock(), resolver=resolver), config=config
    )

    node.save(MOCK_MATRIX_JSON)
    resolver.is_managed.assert_called_once_with("my-study")
    assert file.read_text() == json.dumps(MOCK_MATRIX_JSON)
