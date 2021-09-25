from dataclasses import dataclass

from antarest.matrixstore.service import MatrixService, ISimpleMatrixService
from antarest.study.common.uri_resolver_service import (
    UriResolverService,
)


@dataclass
class ContextServer:
    matrix: ISimpleMatrixService
    resolver: UriResolverService
