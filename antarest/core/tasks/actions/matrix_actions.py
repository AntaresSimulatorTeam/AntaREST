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

"""Task action handlers for matrix operations."""

from __future__ import annotations

import logging
from pathlib import Path

from antarest.core.tasks.action import TaskActionParams, TaskActionRegistry
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import ITaskNotifier
from antarest.service_creator import CoreServices

logger = logging.getLogger(__name__)


class ExportMatricesParams(TaskActionParams):
    matrix_list: list[str]
    dataset_name: str
    export_path: str
    export_id: str


@TaskActionRegistry.register("export_matrices", ExportMatricesParams)
def handle_export_matrices(services: CoreServices, params: ExportMatricesParams, notifier: ITaskNotifier) -> TaskResult:
    matrix_service = services.matrix_service
    export_path = Path(params.export_path)

    try:
        matrix_service.create_matrix_files(matrix_ids=params.matrix_list, export_path=export_path)
        services.file_transfer_manager.set_ready(params.export_id)
        return TaskResult(
            success=True,
            message=f"Matrix dataset {params.dataset_name} successfully exported",
        )
    except Exception as e:
        services.file_transfer_manager.fail(params.export_id, str(e))
        raise e
