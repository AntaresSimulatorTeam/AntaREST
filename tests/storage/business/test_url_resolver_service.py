import os
from unittest.mock import Mock

from antarest.matrixstore.model import MatrixDTO
from antarest.matrixstore.uri_resolver_service import (
    UriResolverService,
)

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
    resolver = UriResolverService(matrix_service=Mock())
    assert "matrix://my-id" == resolver.build_matrix_uri("my-id")


def test_resolve_matrix():
    matrix_service = Mock()
    matrix_service.get.return_value = MOCK_MATRIX_DTO

    resolver = UriResolverService(matrix_service=matrix_service)

    assert MOCK_MATRIX_JSON == resolver.resolve("matrix://my-id")
    matrix_service.get.assert_called_once_with("my-id")

    assert (
        f"1.000000\t2.000000{os.linesep}3.000000\t4.000000{os.linesep}"
        == resolver.resolve("matrix://my-id", False)
    )
