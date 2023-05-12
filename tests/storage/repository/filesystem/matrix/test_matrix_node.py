from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional
from unittest.mock import Mock

import pandas as pd  # type: ignore

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixFrequency,
    MatrixNode,
)

MOCK_MATRIX_JSON = {
    "index": ["1", "2"],
    "columns": ["a", "b"],
    "data": [[1, 2], [3, 4]],
}

MOCK_MATRIX_DTO = [[1, 2], [3, 4]]


class MockMatrixNode(MatrixNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig
    ) -> None:
        super().__init__(
            config=config,
            context=context,
            freq=MatrixFrequency.ANNUAL,
        )

    def parse(
        self,
        file_path: Optional[Path] = None,
        tmp_dir: Optional[TemporaryDirectory] = None,
        return_dataframe: bool = False,
    ) -> JSON:
        return MOCK_MATRIX_JSON

    # def dump(
    #     self, data: Union[bytes, JSON], url: Optional[List[str]] = None
    # ) -> None:
    #     """Dump the matrix data in JSON format to simplify the tests"""
    #     self.config.path.parent.mkdir(exist_ok=True, parents=True)
    #     self.config.path.write_text(
    #         json.dumps(data, indent=2), encoding="utf-8"
    #     )

    def check_errors(
        self, data: str, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass  # not used


class TestMatrixNode:
    def test_normalize(self, tmp_path: Path):
        file = tmp_path / "matrix.json"
        file.touch()

        matrix_service = Mock()
        matrix_service.create.return_value = "my-id"

        resolver = Mock()
        resolver.build_matrix_uri.return_value = "matrix://my-id"

        node = MockMatrixNode(
            context=ContextServer(matrix=matrix_service, resolver=resolver),
            config=FileStudyTreeConfig(
                study_path=file, path=file, study_id="mi-id", version=-1
            ),
        )

        node.normalize()

        # check the result
        assert node.get_link_path().read_text() == "matrix://my-id"
        assert not file.exists()
        matrix_service.create.assert_called_once_with(MOCK_MATRIX_DTO)
        resolver.build_matrix_uri.assert_called_once_with("my-id")

    def test_denormalize(self, tmp_path: Path):
        file = tmp_path / "matrix.json"

        link = file.parent / f"{file.name}.link"
        link.write_text("my-id")

        resolver = Mock()
        resolver.resolve.return_value = MOCK_MATRIX_JSON

        node = MockMatrixNode(
            context=ContextServer(matrix=Mock(), resolver=resolver),
            config=FileStudyTreeConfig(
                study_path=file, path=file, study_id="mi-id", version=-1
            ),
        )

        node.denormalize()

        # check the result
        assert not link.exists()
        actual = pd.read_csv(file, sep="\t", header=None)
        assert actual.values.tolist() == MOCK_MATRIX_JSON["data"]
