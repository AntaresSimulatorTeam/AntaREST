import json
from pathlib import Path
from typing import Optional, List
from unittest.mock import Mock

from antarest.core.custom_types import JSON
from antarest.matrixstore.model import MatrixDTO
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixNode,
)


MOCK_MATRIX_JSON = {
    "width": 2,
    "height": 2,
    "index": ["1", "2"],
    "columns": ["a", "b"],
    "data": [[1, 2], [3, 4]],
}


MOCK_MATRIX_DTO = MatrixDTO(
    width=2,
    height=2,
    index=["1", "2"],
    columns=["a", "b"],
    data=[[1, 2], [3, 4]],
)


class MockMatrixNode(MatrixNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig
    ) -> None:
        super().__init__(config=config, context=context, freq="annual")

    def parse(
        self,
    ) -> JSON:
        return MOCK_MATRIX_JSON

    def _dump_json(self, data: JSON) -> None:
        json.dump(data, self.config.path.open("w"))

    def build(self, config: FileStudyTreeConfig) -> TREE:
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

    resolver = Mock()
    resolver.build_matrix_uri.return_value = "matrix://my-id"

    node = MockMatrixNode(
        context=ContextServer(matrix=matrix_service, resolver=resolver),
        config=FileStudyTreeConfig(
            study_path=file, study_id="mi-id", version=-1
        ),
    )

    node.normalize()
    assert node.get_link_path().read_text() == "matrix://my-id"
    assert not file.exists()
    matrix_service.create.assert_called_once_with(MOCK_MATRIX_DTO)
    resolver.build_matrix_uri.assert_called_once_with("my-id")


def test_denormalize(tmp_path: Path):
    file = tmp_path / "matrix.txt"

    link = file.parent / f"{file.name}.link"
    link.write_text("my-id")

    resolver = Mock()
    resolver.resolve.return_value = MOCK_MATRIX_JSON

    node = MockMatrixNode(
        context=ContextServer(matrix=Mock(), resolver=resolver),
        config=FileStudyTreeConfig(
            study_path=file, study_id="mi-id", version=-1
        ),
    )

    node.denormalize()
    assert not link.exists()
    assert json.loads(file.read_text()) == MOCK_MATRIX_JSON
