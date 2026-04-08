# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.


from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.tasks.service import ITaskService
from antarest.login.service import LoginService
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository
from antarest.matrixstore.service import MatrixService


def build_matrix_service(
    config: Config,
    file_transfer_manager: FileTransferManager,
    task_service: ITaskService,
    user_service: LoginService,
    service: MatrixService | None = None,
) -> MatrixService:
    """
    Matrix module linking dependency

    Args:
        config: server configuration
        file_transfer_manager: File transfer manager
        task_service: Task manager
        user_service: User service for management permissions
        service: used by testing to inject mock. Let None to use true instantiation

    Returns: user facade service

    """
    if service is None:
        repo = MatrixRepository()
        content = MatrixContentRepository(config.storage.matrixstore, config.storage.matrixstore_format)
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

    return service
