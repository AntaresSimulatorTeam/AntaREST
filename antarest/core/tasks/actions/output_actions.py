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

from antarest.core.tasks.action import TaskActionRegistry
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import ITaskNotifier
from antarest.core.utils.utils import StopWatch
from antarest.service_creator import CoreServices

logger = logging.getLogger(__name__)


@TaskActionRegistry.register("archive_output")
def handle_archive_output(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    output_service = services.output_service
    study_id = params["study_id"]
    output_id = params["output_id"]

    try:
        stopwatch = StopWatch()
        output_service._storage.archive_study_output(study_id, output_id)
        stopwatch.log_elapsed(lambda x: logger.info(f"Output {output_id} of study {study_id} archived in {x}s"))
        return TaskResult(
            success=True,
            message=f"Study output {study_id}/{output_id} successfully archived",
        )
    except Exception as e:
        logger.warning(
            f"Could not archive the output {study_id}/{output_id}",
            exc_info=e,
        )
        raise e


@TaskActionRegistry.register("unarchive_output")
def handle_unarchive_output(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    output_service = services.output_service
    study_id = params["study_id"]
    output_id = params["output_id"]

    try:
        stopwatch = StopWatch()
        output_service._storage.unarchive_study_output(study_id, output_id)
        stopwatch.log_elapsed(lambda x: logger.info(f"Output {output_id} of study {study_id} unarchived in {x}s"))
        return TaskResult(
            success=True,
            message=f"Study output {study_id}/{output_id} successfully unarchived",
        )
    except Exception as e:
        logger.warning(
            f"Could not unarchive the output {study_id}/{output_id}",
            exc_info=e,
        )
        raise e


@TaskActionRegistry.register("export_output")
def handle_export_output(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    output_service = services.output_service
    study_uuid = params["study_id"]
    output_uuid = params["output_id"]
    export_path = Path(params["export_path"])
    export_id = params["export_id"]
    study_name = params["study_name"]

    try:
        output_service._storage.export_output(
            study_id=study_uuid,
            output_id=output_uuid,
            target=export_path,
        )
        services.file_transfer_manager.set_ready(export_id)
        return TaskResult(
            success=True,
            message=f"Study output {study_name}/{output_uuid} successfully exported",
        )
    except Exception as e:
        services.file_transfer_manager.fail(export_id, str(e))
        raise e


@TaskActionRegistry.register("aggregate_output")
def handle_aggregate_output(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    from antarest.core.serde.matrix_export import TableExportFormat
    from antarest.study.output.aggregation_queries import (  # type: ignore[import-untyped]
        MCAllAreasQueryFile,
        MCAllLinksQueryFile,
        MCIndAreasQueryFile,
        MCIndLinksQueryFile,
    )
    from antarest.study.storage.df_download import export_df_chunks

    output_service = services.output_service
    uuid = params["study_id"]
    output_id = params["output_id"]
    query_file_type = params["query_file_type"]
    query_file_value = params["query_file_value"]
    frequency_value = params["frequency"]
    export_format_value = params["export_format"]
    columns_names = params["columns_names"]
    ids_to_consider = params["ids_to_consider"]
    file_path = Path(params["file_path"])
    transform_columns_headers = params.get("transform_columns_headers", True)
    mc_years = params.get("mc_years")
    export_id: Optional[str] = params.get("export_id")

    from antarest.study.output.aggregation_queries import MatrixFrequency

    frequency = MatrixFrequency(frequency_value)
    export_format = TableExportFormat(export_format_value)

    # Reconstruct the query file enum
    query_file_map = {
        "MCIndAreasQueryFile": MCIndAreasQueryFile,
        "MCAllAreasQueryFile": MCAllAreasQueryFile,
        "MCIndLinksQueryFile": MCIndLinksQueryFile,
        "MCAllLinksQueryFile": MCAllLinksQueryFile,
    }
    query_file_cls = query_file_map[query_file_type]
    query_file = query_file_cls(query_file_value)

    try:
        stopwatch = StopWatch()
        logger.info(f"Launch aggregation step for output '{output_id}' of study '{uuid}'.")

        results = output_service._storage.aggregate_output_data(
            uuid,
            output_id,
            query_file,
            frequency,
            ids_to_consider,
            columns_names,
            transform_columns_headers,
            mc_years,
        )
        export_df_chunks(output_service._tmp_dir, file_path, results, export_format)

        stopwatch.log_elapsed(lambda x: logger.info(f"Created aggregated outputs file '{file_path}' in {x}s."))

        if export_id:
            services.file_transfer_manager.set_ready(export_id, use_notification=False)

        logger.info(f"Aggregated output file '{file_path}' is ready for download.")
        return TaskResult(
            success=True,
            message=f"Successfully aggregated output data for study '{uuid}'. Results are stored in '{file_path}'.",
        )

    except Exception as e:
        if export_id:
            services.file_transfer_manager.fail(export_id, str(e))
        raise e


@TaskActionRegistry.register("materialize_output_view")
def handle_materialize_output_view(
    services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier
) -> TaskResult:
    from antarest.study.output.output_service import OutputVariablesViewMaterializationTask
    from antarest.study.output.variables_management import OutputItemId

    output_service = services.output_service
    study_id = params["study_id"]
    output_id = params["output_id"]
    variable_name = params["variable_name"]
    frequency_value = params["frequency"]
    output_item_id_data = params["output_item_id"]

    from pydantic import TypeAdapter

    from antarest.study.output.aggregation_queries import MatrixFrequency

    frequency = MatrixFrequency(frequency_value)
    output_item_id: OutputItemId = TypeAdapter(OutputItemId).validate_python(output_item_id_data)

    task = OutputVariablesViewMaterializationTask(
        study_id, output_id, output_service, variable_name, frequency, output_item_id
    )
    return task.run_task(notifier)
