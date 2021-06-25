from pathlib import Path
from unittest.mock import Mock

from antarest.common.jwt import DEFAULT_ADMIN_USER
from antarest.matrixstore.model import MatrixDTO, MatrixFreq
from antarest.matrixstore.service import MatrixService
from antarest.storage.business.uri_resolver_service import UriResolverService

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


def test_build_studyfile_uri():
    path = Path() / "my-study/my/file"

    resolver = UriResolverService(config=Mock(), matrix_service=Mock())
    res = resolver.build_studyfile_uri(path, "my-study")
    assert "studyfile://my-study/my/file" == res


def test_build_matrix_uri():
    resolver = UriResolverService(config=Mock(), matrix_service=Mock())
    assert "matrix://my-id" == resolver.build_matrix_uri("my-id")


def test_resolve_file(tmp_path: Path):
    file = tmp_path / "my-study/my/file"
    file.parent.mkdir(parents=True)
    file.write_text("File Content")

    storage_service = Mock()
    storage_service.get_study_path.return_value = tmp_path / "my-study"

    resolver = UriResolverService(config=Mock(), matrix_service=Mock())
    resolver.storage_service = storage_service

    assert "File Content" == resolver.resolve("studyfile://my-study/my/file")
    storage_service.get_study_path.assert_called_once_with(
        "my-study", DEFAULT_ADMIN_USER
    )


def test_resolve_matrix():
    matrix_service = Mock()
    matrix_service.get.return_value = MOCK_MATRIX_DTO

    resolver = UriResolverService(config=Mock(), matrix_service=matrix_service)

    assert MOCK_MATRIX_JSON == resolver.resolve("matrix://my-id")
    matrix_service.get.assert_called_once_with("my-id")
