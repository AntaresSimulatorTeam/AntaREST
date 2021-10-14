from typing import Optional

from fastapi import FastAPI
from fastapi_jwt_auth.exceptions import AuthJWTException  # type: ignore

from antarest.core.config import Config
from antarest.login.service import LoginService
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
    MatrixDataSetRepository,
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
        dataset_repo = MatrixDataSetRepository()

        service = MatrixService(
            repo=repo,
            repo_dataset=dataset_repo,
            matrix_content_repository=content,
            user_service=user_service,
        )

    application.include_router(create_matrix_api(service, config))
    return service
