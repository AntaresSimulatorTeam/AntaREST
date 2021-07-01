import json
from pathlib import Path
from typing import Optional, List
from unittest.mock import Mock

from antarest.common.custom_types import JSON
from antarest.matrixstore.model import MatrixDTO, MatrixFreq
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.matrix.matrix import MatrixNode


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


class MockMatrixNode(MatrixNode):
    def __init__(self, context: ContextServer, config: StudyConfig) -> None:
        super().__init__(config=config, context=context, freq="annual")

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> JSON:
        return MOCK_MATRIX_JSON

    def dump(self, data: JSON, url: Optional[List[str]] = None) -> None:
        json.dump(data, self.config.path.open("w"))

    def build(self, config: StudyConfig) -> TREE:
        pass  # not used

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass  # not used


def test_normalize(tmp_path: Path):
    file = tmp_path / "matrix.txt"
    file.touch()

    matrix_service = Mock()
    matrix_service.create.return_value = "my-id"

    node = MockMatrixNode(
        context=ContextServer(matrix=matrix_service, resolver=Mock()),
        config=StudyConfig(study_path=file, study_id="mi-id"),
    )

    node.normalize()
    assert node.get_link_path().read_text() == "my-id"
    assert not file.exists()
    matrix_service.create.assert_called_once_with(MOCK_MATRIX_DTO)


def test_denormalize(tmp_path: Path):
    file = tmp_path / "matrix.txt"

    link = file.parent / f"{file.name}.link"
    link.write_text("my-id")

    matrix_service = Mock()
    matrix_service.get.return_value = MOCK_MATRIX_DTO

    node = MockMatrixNode(
        context=ContextServer(matrix=matrix_service, resolver=Mock()),
        config=StudyConfig(study_path=file, study_id="mi-id"),
    )

    node.denormalize()
    assert not link.exists()
    assert json.loads(file.read_text()) == MOCK_MATRIX_JSON
