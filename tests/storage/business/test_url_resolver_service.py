from pathlib import Path
from unittest.mock import Mock

from antarest.core.config import Config
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.matrixstore.model import MatrixDTO
from antarest.storage.business.uri_resolver_service import UriResolverService
from antarest.storage.service import StorageService

MOCK_MATRIX_JSON = {
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


def test_build_matrix_uri():
    resolver = UriResolverService(config=Mock(), matrix_service=Mock())
    assert "matrix://my-id" == resolver.build_matrix_uri("my-id")


def test_resolve_matrix():
    matrix_service = Mock()
    matrix_service.get.return_value = MOCK_MATRIX_DTO

    resolver = UriResolverService(config=Mock(), matrix_service=matrix_service)

    assert MOCK_MATRIX_JSON == resolver.resolve("matrix://my-id")
    matrix_service.get.assert_called_once_with("my-id")
