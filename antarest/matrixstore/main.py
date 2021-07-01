from typing import Optional

from fastapi import FastAPI
from fastapi_jwt_auth.exceptions import AuthJWTException  # type: ignore

from antarest.common.config import Config
from antarest.login.service import LoginService
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
    MatrixMetadataRepository,
)
from antarest.matrixstore.service import MatrixService
from antarest.matrixstore.web import create_matrix_api


def build_matrixstore(
    application: FastAPI,
    config: Config,
    user_service: LoginService,
    service: Optional[MatrixService] = None,
) -> MatrixService:
    """
    Matrix module linking dependency

    Args:
        application: flask application
        config: server configuration
        user_service: User service for management permissions
        service: used by testing to inject mock. Let None to use true instantiation

    Returns: user facade service

    """

    if service is None:
        repo = MatrixRepository()
        content = MatrixContentRepository(config)
        metadata_repo = MatrixMetadataRepository()

        service = MatrixService(
            repo=repo,
            repo_meta=metadata_repo,
            content=content,
            user_service=user_service,
        )

    application.include_router(create_matrix_api(service, config))
    return service
