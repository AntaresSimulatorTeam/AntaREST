from typing import Optional

from fastapi import FastAPI
from fastapi_jwt_auth.exceptions import AuthJWTException  # type: ignore

from antarest.common.config import Config
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
)
from antarest.matrixstore.service import MatrixService
from antarest.matrixstore.web import create_matrix_api


def build_matrixstore(
    application: FastAPI,
    config: Config,
    service: Optional[MatrixService] = None,
) -> MatrixService:
    """
    Matrix module linking dependency

    Args:
        application: flask application
        config: server configuration
        service: used by testing to inject mock. Let None to use true instantiation

    Returns: user facade service

    """

    if service is None:
        repo = MatrixRepository()
        content = MatrixContentRepository(config)

        service = MatrixService(repo=repo, content=content)

    application.include_router(create_matrix_api(service, config))
    return service
