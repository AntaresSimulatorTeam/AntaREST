import textwrap
import typing as t
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.core.exceptions import ChildNotFoundError
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix


class TestInputSeriesMatrix:
    @pytest.fixture(name="my_study_config")
    def fixture_my_study_config(self, tmp_path: Path) -> FileStudyTreeConfig:
        """
        Construct a FileStudyTreeConfig object for a dummy study stored in a temporary directory.
        """
        return FileStudyTreeConfig(
            study_path=tmp_path,
            path=tmp_path / "input.txt",
            study_id="df0a8aa9-6c6f-4e8b-a84e-45de2fb29cd3",
            version=800,
        )

    def test_load(self, my_study_config: FileStudyTreeConfig) -> None:
        file = my_study_config.path
        content = textwrap.dedent(
            """\
            100000\t100000\t0.010000\t0.010000\t0\t0\t0\t3.14
            100000\t100000\t0.010000\t0.010000\t0\t0\t0\t6.28
            """
        )
        file.write_text(content)

        node = InputSeriesMatrix(context=Mock(), config=my_study_config, nb_columns=8)
        actual = node.load()
        expected = {
            "columns": [0, 1, 2, 3, 4, 5, 6, 7],
            "data": [
                [100000.0, 100000.0, 0.01, 0.01, 0.0, 0.0, 0.0, 3.14],
                [100000.0, 100000.0, 0.01, 0.01, 0.0, 0.0, 0.0, 6.28],
            ],
            "index": [0, 1],
        }
        assert actual == expected

    def test_load__file_not_found(self, my_study_config: FileStudyTreeConfig) -> None:
        node = InputSeriesMatrix(context=Mock(), config=my_study_config)
        with pytest.raises(ChildNotFoundError) as ctx:
            node.load()
        err_msg = str(ctx.value)
        assert "input.txt" in err_msg
        assert my_study_config.study_id in err_msg
        assert "not found" in err_msg.lower()

    def test_load__link_to_matrix(self, my_study_config: FileStudyTreeConfig) -> None:
        link = my_study_config.path.with_suffix(".txt.link")
        matrix_uri = "matrix://54e252eb14c0440055c82520c338376ff436e1d7ed6cb7283084c89e2e472c42"
        matrix_obj = {
            "data": [[1, 2], [3, 4]],
            "index": [0, 1],
            "columns": [0, 1],
        }
        link.write_text(matrix_uri)

        def resolve(uri: str, formatted: bool = True) -> t.Dict[str, t.Any]:
            assert uri == matrix_uri
            assert formatted is True
            return matrix_obj

        context = ContextServer(
            matrix=Mock(spec=ISimpleMatrixService),
            resolver=Mock(spec=UriResolverService, resolve=resolve),
        )

        node = InputSeriesMatrix(context=context, config=my_study_config)
        actual = node.load()
        assert actual == matrix_obj

    def test_save(self, my_study_config: FileStudyTreeConfig) -> None:
        node = InputSeriesMatrix(context=Mock(), config=my_study_config)
        node.dump({"columns": [0, 1], "data": [[1, 2], [3, 4]], "index": [0, 1]})
        actual = my_study_config.path.read_text()
        expected = textwrap.dedent(
            """\
            1\t2
            3\t4
            """
        )
        assert actual == expected
