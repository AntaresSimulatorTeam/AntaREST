from dataclasses import dataclass

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import (
    UriResolverService,
)


@dataclass
class ContextServer:
    matrix: ISimpleMatrixService
    resolver: UriResolverService
