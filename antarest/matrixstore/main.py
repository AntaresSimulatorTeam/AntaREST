from typing import Optional

from fastapi import FastAPI
from fastapi_jwt_auth.exceptions import AuthJWTException  # type: ignore

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.tasks.service import ITaskService
from antarest.login.service import LoginService
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
    MatrixDataSetRepository,
)
from antarest.matrixstore.service import MatrixService
from antarest.matrixstore.web import create_matrix_api


def build_matrixstore(
    application: Optional[FastAPI],
    config: Config,
    file_transfer_manager: FileTransferManager,
    task_service: ITaskService,
    user_service: LoginService,
    service: Optional[MatrixService] = None,
) -> MatrixService:
    """
    Matrix module linking dependency

    Args:
        application: flask application
        config: server configuration
        file_transfer_manager: File transfer manager
        task_service: Task manager
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
            file_transfer_manager=file_transfer_manager,
            task_service=task_service,
            config=config,
        )

    if application:
        application.include_router(
            create_matrix_api(service, file_transfer_manager, config)
        )

    return service
