# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import collections
import io
import logging
from http import HTTPStatus
from pathlib import Path
from typing import Any, List, Sequence

from fastapi import APIRouter, Depends, File, Query, Request
from starlette.responses import FileResponse

from antarest.core.config import Config
from antarest.core.utils.utils import sanitize_string, sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.study.business.aggregator_management import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
)
from antarest.study.model import ExportFormat, StudyDownloadDTO, StudySimResultDTO
from antarest.study.storage.df_download import TableExportFormat, export_file
from antarest.study.storage.output_service import OutputService
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI

logger = logging.getLogger(__name__)

DEFAULT_EXPORT_FORMAT = Query(TableExportFormat.CSV, alias="format", description="Export format", title="Export Format")


def _split_comma_separated_values(value: str, *, default: Sequence[str] = ()) -> Sequence[str]:
    """Split a comma-separated list of values into an ordered set of strings."""
    values = value.split(",") if value else default
    # drop whitespace around values
    values = [v.strip() for v in values]
    # remove duplicates and preserve order (to have a deterministic result for unit tests).
    return list(collections.OrderedDict.fromkeys(values))


def create_output_routes(output_service: OutputService, config: Config) -> APIRouter:
    """
    Endpoint implementation for outputs management

    Args:
        output_service: output service facade to handle request
        config: main server configuration

    Returns:
        The FastAPI route for Study data management
    """
    bp = APIRouter(prefix="/v1")

    # noinspection PyShadowingBuiltins
    @bp.post(
        "/studies/{uuid}/output",
        status_code=HTTPStatus.ACCEPTED,
        tags=[APITag.study_outputs],
        summary="Import Output",
        response_model=str,
    )
    def import_output(uuid: str, output: bytes = File(...)) -> Any:
        logger.info(f"Importing output for study {uuid}")
        uuid_sanitized = sanitize_uuid(uuid)

        zip_binary = io.BytesIO(output)

        output_id = output_service.import_output(uuid_sanitized, zip_binary)
        return output_id

    @bp.get(
        "/studies/{study_id}/outputs/{output_id}/variables",
        tags=[APITag.study_outputs],
        summary="Get outputs data variables",
    )
    def output_variables_information(study_id: str, output_id: str) -> Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Fetching whole output of the simulation {output_id} for study {study_id}")
        return output_service.output_variables_information(study_uuid=study_id, output_uuid=output_id)

    @bp.get(
        "/studies/{study_id}/outputs/{output_id}/export",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
    )
    def output_export(study_id: str, output_id: str) -> Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Fetching whole output of the simulation {output_id} for study {study_id}")
        return output_service.export_output(study_uuid=study_id, output_uuid=output_id)

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/download",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
    )
    def output_download(
        study_id: str,
        output_id: str,
        data: StudyDownloadDTO,
        request: Request,
        use_task: bool = False,
        tmp_export_file: Path = Depends(output_service._file_transfer_manager.request_tmp_file),
    ) -> Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Fetching batch outputs of simulation {output_id} for study {study_id}")
        accept = request.headers["Accept"]
        filetype = ExportFormat.from_dto(accept)

        content = output_service.download_outputs(
            study_id,
            output_id,
            data,
            use_task,
            filetype,
            tmp_export_file,
        )
        return content

    @bp.delete(
        "/studies/{study_id}/outputs/{output_id}",
        tags=[APITag.study_outputs],
        summary="Delete a simulation output",
    )
    def delete_output(study_id: str, output_id: str) -> None:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"FDeleting output {output_id} from study {study_id}")
        output_service.delete_output(study_id, output_id)

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/_archive",
        tags=[APITag.study_outputs],
        summary="Archive output",
    )
    def archive_output(study_id: str, output_id: str) -> Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Archiving of the output {output_id} of the study {study_id}")

        content = output_service.archive_output(study_id, output_id)
        return content

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/_unarchive",
        tags=[APITag.study_outputs],
        summary="Unarchive output",
    )
    def unarchive_output(study_id: str, output_id: str) -> Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Unarchiving of the output {output_id} of the study {study_id}")

        content = output_service.unarchive_output(study_id, output_id, False)
        return content

    @bp.get(
        "/private/studies/{study_id}/outputs/{output_id}/digest-ui",
        tags=[APITag.study_outputs],
        summary="Display an output digest file for the front-end",
        response_model=DigestUI,
    )
    def get_digest_file(study_id: str, output_id: str) -> DigestUI:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Retrieving the digest file for the output {output_id} of the study {study_id}")
        return output_service.get_digest_file(study_id, output_id)

    @bp.get(
        "/studies/{study_id}/outputs",
        summary="Get global information about a study simulation result",
        tags=[APITag.study_outputs],
        response_model=List[StudySimResultDTO],
    )
    def sim_result(study_id: str) -> Any:
        logger.info(f"Fetching output list for study {study_id}")
        study_id = sanitize_uuid(study_id)
        content = output_service.get_study_sim_result(study_id)
        return content

    @bp.get(
        "/studies/{uuid}/outputs/{output_id}/aggregate/areas/mc-ind",
        tags=[APITag.study_outputs],
        summary="Retrieve Aggregated Areas Raw Data from Study Economy MCs individual Outputs",
    )
    def aggregate_areas_raw_data(
        uuid: str,
        output_id: str,
        query_file: MCIndAreasQueryFile,
        frequency: MatrixFrequency,
        mc_years: str = "",
        areas_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,
    ) -> FileResponse:
        # noinspection SpellCheckingInspection
        """
        Create an aggregation of areas raw data

        Parameters:

        - `uuid`: study ID
        - `output_id`: the output ID aka the simulation ID
        - `query_file`: "values", "details", "details-STstorage", "details-res"
        - `frequency`: "hourly", "daily", "weekly", "monthly", "annual"
        - `mc_years`: which Monte Carlo years to be selected. If empty, all are selected (comma separated)
        - `areas_ids`: which areas to be selected. If empty, all are selected (comma separated)
        - `columns_names`: names or regexes (if `query_file` is of type `details`) to select columns (comma separated)
        - `export_format`: Returned file format (csv by default).

        Returns:
            FileResponse that corresponds to a dataframe with the aggregated areas raw data
        """
        logger.info(
            f"Aggregating areas output data for study {uuid}, output {output_id},"
            f"from files '{query_file}-{frequency}.txt'"
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        df_matrix = output_service.aggregate_output_data(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(areas_ids),
            aggregation_results_max_size=config.storage.aggregation_results_max_size,
            mc_years=[int(mc_year) for mc_year in _split_comma_separated_values(mc_years)],
        )

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return export_file(
            df_matrix, output_service._file_transfer_manager, export_format, False, True, download_name, download_log
        )

    @bp.get(
        "/studies/{uuid}/areas/aggregate/mc-ind/{output_id}",
        tags=[APITag.study_outputs],
        summary="Retrieve Aggregated Areas Raw Data from Study Economy MCs individual Outputs",
        include_in_schema=False,
    )
    def redirect_aggregate_areas_raw_data(
        uuid: str,
        output_id: str,
        query_file: MCIndAreasQueryFile,
        frequency: MatrixFrequency,
        mc_years: str = "",
        areas_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,
    ) -> FileResponse:
        return aggregate_areas_raw_data(
            uuid, output_id, query_file, frequency, mc_years, areas_ids, columns_names, export_format
        )

    @bp.get(
        "/studies/{uuid}/outputs/{output_id}/aggregate/links/mc-ind",
        tags=[APITag.study_outputs],
        summary="Retrieve Aggregated Links Raw Data from Study Economy MCs individual Outputs",
    )
    def aggregate_links_raw_data(
        uuid: str,
        output_id: str,
        query_file: MCIndLinksQueryFile,
        frequency: MatrixFrequency,
        mc_years: str = "",
        links_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,
    ) -> FileResponse:
        """
        Create an aggregation of links raw data

        Parameters:

        - `uuid`: study ID
        - `output_id`: the output ID aka the simulation ID
        - `query_file`: "values" (currently the only available option)
        - `frequency`: "hourly", "daily", "weekly", "monthly", "annual"
        - `mc_years`: which Monte Carlo years to be selected. If empty, all are selected (comma separated)
        - `links_ids`: which links to be selected (ex: "be - fr"). If empty, all are selected (comma separated)
        - `columns_names`: names or regexes (if `query_file` is of type `details`) to select columns (comma separated)
        - `export_format`: Returned file format (csv by default).

        Returns:
            FileResponse that corresponds to a dataframe with the aggregated links raw data
        """
        logger.info(
            f"Aggregating links output data for study {uuid}, output {output_id},"
            f"from files '{query_file}-{frequency}.txt'"
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        df_matrix = output_service.aggregate_output_data(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(links_ids),
            aggregation_results_max_size=config.storage.aggregation_results_max_size,
            mc_years=[int(mc_year) for mc_year in _split_comma_separated_values(mc_years)],
        )

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return export_file(
            df_matrix,
            output_service._file_transfer_manager,
            export_format,
            False,
            True,
            download_name,
            download_log,
        )

    @bp.get(
        "/studies/{uuid}/links/aggregate/mc-ind/{output_id}",
        tags=[APITag.study_outputs],
        summary="Retrieve Aggregated Links Raw Data from Study Economy MCs individual Outputs",
        include_in_schema=False,
    )
    def redirect_aggregate_links_raw_data(
        uuid: str,
        output_id: str,
        query_file: MCIndLinksQueryFile,
        frequency: MatrixFrequency,
        mc_years: str = "",
        links_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,
    ) -> FileResponse:
        return aggregate_links_raw_data(
            uuid, output_id, query_file, frequency, mc_years, links_ids, columns_names, export_format
        )

    @bp.get(
        "/studies/{uuid}/outputs/{output_id}/aggregate/areas/mc-all",
        tags=[APITag.study_outputs],
        summary="Retrieve Aggregated Areas Raw Data from Study Economy MCs All Outputs",
    )
    def aggregate_areas_raw_data__all(
        uuid: str,
        output_id: str,
        query_file: MCAllAreasQueryFile,
        frequency: MatrixFrequency,
        areas_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,
    ) -> FileResponse:
        # noinspection SpellCheckingInspection
        """
        Create an aggregation of areas raw data in mc-all

        Parameters:

        - `uuid`: study ID
        - `output_id`: the output ID aka the simulation ID
        - `query_file`: "values", "details", "details-STstorage", "details-res", "id"
        - `frequency`: "hourly", "daily", "weekly", "monthly", "annual"
        - `areas_ids`: which areas to be selected. If empty, all are selected (comma separated)
        - `columns_names`: names or regexes (if `query_file` is of type `details`) to select columns (comma separated)
        - `export_format`: Returned file format (csv by default).

        Returns:
            FileResponse that corresponds to a dataframe with the aggregated areas raw data
        """
        logger.info(
            f"Aggregating areas output data for study {uuid}, output {output_id},"
            f"from files '{query_file}-{frequency}.txt'"
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        df_matrix = output_service.aggregate_output_data(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(areas_ids),
            aggregation_results_max_size=config.storage.aggregation_results_max_size,
        )

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return export_file(
            df_matrix,
            output_service._file_transfer_manager,
            export_format,
            False,
            True,
            download_name,
            download_log,
        )

    @bp.get(
        "/studies/{uuid}/areas/aggregate/mc-all/{output_id}",
        tags=[APITag.study_outputs],
        summary="Retrieve Aggregated Areas Raw Data from Study Economy MCs All Outputs",
        include_in_schema=False,
    )
    def redirect_aggregate_areas_raw_data__all(
        uuid: str,
        output_id: str,
        query_file: MCAllAreasQueryFile,
        frequency: MatrixFrequency,
        areas_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,
    ) -> FileResponse:
        return aggregate_areas_raw_data__all(
            uuid, output_id, query_file, frequency, areas_ids, columns_names, export_format
        )

    @bp.get(
        "/studies/{uuid}/outputs/{output_id}/aggregate/links/mc-all",
        tags=[APITag.study_outputs],
        summary="Retrieve Aggregated Links Raw Data from Study Economy MC-All Outputs",
    )
    def aggregate_links_raw_data__all(
        uuid: str,
        output_id: str,
        query_file: MCAllLinksQueryFile,
        frequency: MatrixFrequency,
        links_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,
    ) -> FileResponse:
        """
        Create an aggregation of links in mc-all

        Parameters:

        - `uuid`: study ID
        - `output_id`: the output ID aka the simulation ID
        - `query_file`: "values", "id"
        - `frequency`: "hourly", "daily", "weekly", "monthly", "annual"
        - `links_ids`: which links to be selected (ex: "be - fr"). If empty, all are selected (comma separated)
        - `columns_names`: names or regexes (if `query_file` is of type `details`) to select columns (comma separated)
        - `export_format`: Returned file format (csv by default).

        Returns:
            FileResponse that corresponds to a dataframe with the aggregated links raw data
        """
        logger.info(
            f"Aggregating links mc-all data for study {uuid}, output {output_id},"
            f"from files '{query_file}-{frequency}.txt'"
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        df_matrix = output_service.aggregate_output_data(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(links_ids),
            aggregation_results_max_size=config.storage.aggregation_results_max_size,
        )

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return export_file(
            df_matrix, output_service._file_transfer_manager, export_format, False, True, download_name, download_log
        )

    @bp.get(
        "/studies/{uuid}/links/aggregate/mc-all/{output_id}",
        tags=[APITag.study_outputs],
        summary="Retrieve Aggregated Links Raw Data from Study Economy MC-All Outputs",
        include_in_schema=False,
    )
    def redirect_aggregate_links_raw_data__all(
        uuid: str,
        output_id: str,
        query_file: MCAllLinksQueryFile,
        frequency: MatrixFrequency,
        links_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,
    ) -> FileResponse:
        return aggregate_links_raw_data__all(
            uuid, output_id, query_file, frequency, links_ids, columns_names, export_format
        )

    return bp
