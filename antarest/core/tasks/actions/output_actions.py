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

"""Task action handlers for output operations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from antarest.core.tasks.action import TaskActionParams, TaskActionRegistry
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import ITaskNotifier
from antarest.core.utils.utils import StopWatch
from antarest.service_creator import CoreServices

logger = logging.getLogger(__name__)


class ArchiveOutputParams(TaskActionParams):
    study_id: str
    output_id: str


class UnarchiveOutputParams(TaskActionParams):
    study_id: str
    output_id: str


class ExportOutputParams(TaskActionParams):
    study_id: str
    output_id: str
    export_path: str
    export_id: str
    study_name: str


class AggregateOutputParams(TaskActionParams):
    study_id: str
    output_id: str
    query_file_type: str
    query_file_value: str
    frequency: str
    export_format: str
    columns_names: list[str]
    ids_to_consider: list[str]
    file_path: str
    transform_columns_headers: bool = True
    mc_years: Optional[list[int]] = None
    export_id: Optional[str] = None


class MaterializeOutputViewParams(TaskActionParams):
    study_id: str
    output_id: str
    variable_name: str
    frequency: str
    output_item_id: Any


@TaskActionRegistry.register("archive_output", ArchiveOutputParams)
def handle_archive_output(services: CoreServices, params: ArchiveOutputParams, notifier: ITaskNotifier) -> TaskResult:
    output_service = services.output_service

    try:
        stopwatch = StopWatch()
        output_service._storage.archive_study_output(params.study_id, params.output_id)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Output {params.output_id} of study {params.study_id} archived in {x}s")
        )
        return TaskResult(
            success=True,
            message=f"Study output {params.study_id}/{params.output_id} successfully archived",
        )
    except Exception as e:
        logger.warning(
            f"Could not archive the output {params.study_id}/{params.output_id}",
            exc_info=e,
        )
        raise e


@TaskActionRegistry.register("unarchive_output", UnarchiveOutputParams)
def handle_unarchive_output(
    services: CoreServices, params: UnarchiveOutputParams, notifier: ITaskNotifier
) -> TaskResult:
    output_service = services.output_service

    try:
        stopwatch = StopWatch()
        output_service._storage.unarchive_study_output(params.study_id, params.output_id)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Output {params.output_id} of study {params.study_id} unarchived in {x}s")
        )
        return TaskResult(
            success=True,
            message=f"Study output {params.study_id}/{params.output_id} successfully unarchived",
        )
    except Exception as e:
        logger.warning(
            f"Could not unarchive the output {params.study_id}/{params.output_id}",
            exc_info=e,
        )
        raise e


@TaskActionRegistry.register("export_output", ExportOutputParams)
def handle_export_output(services: CoreServices, params: ExportOutputParams, notifier: ITaskNotifier) -> TaskResult:
    output_service = services.output_service
    export_path = Path(params.export_path)

    try:
        output_service._storage.export_output(
            study_id=params.study_id,
            output_id=params.output_id,
            target=export_path,
        )
        services.file_transfer_manager.set_ready(params.export_id)
        return TaskResult(
            success=True,
            message=f"Study output {params.study_name}/{params.output_id} successfully exported",
        )
    except Exception as e:
        services.file_transfer_manager.fail(params.export_id, str(e))
        raise e


@TaskActionRegistry.register("aggregate_output", AggregateOutputParams)
def handle_aggregate_output(
    services: CoreServices, params: AggregateOutputParams, notifier: ITaskNotifier
) -> TaskResult:
    from antarest.core.serde.matrix_export import TableExportFormat
    from antarest.study.output.aggregation_queries import (  # type: ignore[import-untyped]
        MatrixFrequency,
        MCAllAreasQueryFile,
        MCAllLinksQueryFile,
        MCIndAreasQueryFile,
        MCIndLinksQueryFile,
    )
    from antarest.study.storage.df_download import export_df_chunks

    output_service = services.output_service
    file_path = Path(params.file_path)
    frequency = MatrixFrequency(params.frequency)
    export_format = TableExportFormat(params.export_format)

    # Reconstruct the query file enum
    query_file_map = {
        "MCIndAreasQueryFile": MCIndAreasQueryFile,
        "MCAllAreasQueryFile": MCAllAreasQueryFile,
        "MCIndLinksQueryFile": MCIndLinksQueryFile,
        "MCAllLinksQueryFile": MCAllLinksQueryFile,
    }
    query_file_cls = query_file_map[params.query_file_type]
    query_file = query_file_cls(params.query_file_value)

    try:
        stopwatch = StopWatch()
        logger.info(f"Launch aggregation step for output '{params.output_id}' of study '{params.study_id}'.")

        results = output_service._storage.aggregate_output_data(
            params.study_id,
            params.output_id,
            query_file,
            frequency,
            params.ids_to_consider,
            params.columns_names,
            params.transform_columns_headers,
            params.mc_years,
        )
        export_df_chunks(output_service._tmp_dir, file_path, results, export_format)

        stopwatch.log_elapsed(lambda x: logger.info(f"Created aggregated outputs file '{file_path}' in {x}s."))

        if params.export_id:
            services.file_transfer_manager.set_ready(params.export_id, use_notification=False)

        logger.info(f"Aggregated output file '{file_path}' is ready for download.")
        return TaskResult(
            success=True,
            message=f"Successfully aggregated output data for study '{params.study_id}'. Results are stored in '{file_path}'.",
        )

    except Exception as e:
        if params.export_id:
            services.file_transfer_manager.fail(params.export_id, str(e))
        raise e


@TaskActionRegistry.register("materialize_output_view", MaterializeOutputViewParams)
def handle_materialize_output_view(
    services: CoreServices, params: MaterializeOutputViewParams, notifier: ITaskNotifier
) -> TaskResult:
    from pydantic import TypeAdapter

    from antarest.study.output.aggregation_queries import MatrixFrequency
    from antarest.study.output.output_service import OutputVariablesViewMaterializationTask
    from antarest.study.output.variables_management import OutputItemId

    output_service = services.output_service
    frequency = MatrixFrequency(params.frequency)
    output_item_id: OutputItemId = TypeAdapter(OutputItemId).validate_python(params.output_item_id)

    task = OutputVariablesViewMaterializationTask(
        params.study_id, params.output_id, output_service, params.variable_name, frequency, output_item_id
    )
    return task.run_task(notifier)
