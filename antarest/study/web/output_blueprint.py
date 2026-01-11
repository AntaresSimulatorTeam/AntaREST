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
import collections
import logging
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any, Sequence

import pandas as pd
from fastapi import APIRouter, Depends, Query, UploadFile
from pydantic import TypeAdapter
from starlette.responses import FileResponse, Response

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.serde.json import to_json
from antarest.core.serde.matrix_export import TableExportFormat
from antarest.core.utils.dict_utils import remove_nones
from antarest.core.utils.utils import sanitize_string, sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.model import MatrixFrequency, MatrixIndex, StudyDownloadDTO, StudySimResultDTO
from antarest.study.output.output_model import (
    OutputVariablesInformation,
    OutputVariablesList,
    OutputVariablesType,
    OutputVariablesViewResponse,
)
from antarest.study.output.output_service import OutputService
from antarest.study.output.utils import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
)
from antarest.study.output.variables_management import OutputItemId
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI

logger = logging.getLogger(__name__)

DEFAULT_EXPORT_FORMAT = Query(TableExportFormat.CSV, alias="format", description="Export format", title="Export Format")

download_expiration_time_query: Any = Query(
    gt=0,
    lt=1000,
    description="Expiration time for the download file (in minutes)",
)

DEFAULT_DOWNLOAD_EXPIRATION_TIME = 60  # in minutes


def _split_comma_separated_values(value: str, *, default: Sequence[str] = ()) -> Sequence[str]:
    """Split a comma-separated list of values into an ordered set of strings."""
    values = value.split(",") if value else default
    # drop whitespace around values
    values = [v.strip() for v in values]
    # remove duplicates and preserve order (to have a deterministic result for unit tests).
    return list(collections.OrderedDict.fromkeys(values))


_ITEM_ID_TYPE_ADAPTER: TypeAdapter[OutputItemId] = TypeAdapter(OutputItemId)


def _to_item_id(
    type: OutputVariablesType,
    area_id: str | None = None,
    area_from_id: str | None = None,
    area_to_id: str | None = None,
    thermal_id: str | None = None,
    renewable_id: str | None = None,
    st_storage_id: str | None = None,
) -> OutputItemId:
    return _ITEM_ID_TYPE_ADAPTER.validate_python(
        remove_nones(
            {
                "type": type,
                "area_id": area_id,
                "area_from_id": area_from_id,
                "area_to_id": area_to_id,
                "thermal_id": thermal_id,
                "renewable_id": renewable_id,
                "st_storage_id": st_storage_id,
            }
        )
    )


def create_output_routes(
    output_service: OutputService, file_transfer_manager: FileTransferManager, config: Config
) -> APIRouter:
    """
    Endpoint implementation for outputs management

    Args:
        output_service: output service facade to handle request
        config: main server configuration

    Returns:
        The FastAPI route for Study data management
    """
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", tags=[APITag.study_outputs], dependencies=[auth.required()])

    # noinspection PyShadowingBuiltins
    @bp.post(
        "/studies/{uuid}/output",
        status_code=HTTPStatus.ACCEPTED,
        summary="Import Output",
    )
    def import_output(uuid: str, output: UploadFile) -> str | None:
        logger.info(f"Importing output for study {uuid}")
        uuid_sanitized = sanitize_uuid(uuid)
        output_id = output_service.import_output(uuid_sanitized, output.file)
        return output_id

    @bp.get(
        "/studies/{study_id}/outputs/{output_id}/variables",
        summary="Get outputs data variables",
    )
    def output_variables_information(study_id: str, output_id: str) -> OutputVariablesInformation:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Fetching whole output of the simulation {output_id} for study {study_id}")
        return output_service.get_output_variables_information(study_id, output_id)

    @bp.get(
        "/studies/{study_id}/outputs/{output_id}/export",
        summary="Get outputs data",
    )
    def output_export(study_id: str, output_id: str) -> FileDownloadTaskDTO:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Fetching whole output of the simulation {output_id} for study {study_id}")
        return output_service.export_output(study_uuid=study_id, output_uuid=output_id)

    @bp.get(
        "/studies/{uuid}/output/{output_id}/time-index",
        summary="Get time index for output matrices by frequency",
    )
    def get_output_time_index(
        uuid: str,
        output_id: str,
        frequency: MatrixFrequency = Query(
            MatrixFrequency.HOURLY,
            description="Temporal frequency (hourly, daily, weekly, monthly, annual)",
        ),
    ) -> MatrixIndex:
        """
        Get the time indexing information (start date, step count, etc.) for output matrices
        at a specific temporal frequency.

        Args:
        - `uuid`: The UUID of the study.
        - `output_id`: The ID of the output simulation.
        - `frequency`: The temporal granularity (hourly, daily, weekly, monthly, or annual).

        Returns:
        - MatrixIndex containing start_date, steps, first_week_size, and level.
        """
        study_id = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)
        logger.info(f"Getting time index for study '{study_id}', output '{output_id}' at frequency '{frequency}'")
        return output_service.get_output_time_index(study_id, output_id, frequency)

    @bp.post("/studies/{study_id}/outputs/{output_id}/download", summary="Get outputs data")
    def output_download(
        study_id: str,
        output_id: str,
        data: StudyDownloadDTO,
        use_task: bool = Query(default=False, deprecated=True),
        tmp_export_file: Path = Depends(file_transfer_manager.request_tmp_file),
    ) -> FileResponse:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Fetching batch outputs of simulation {output_id} for study {study_id}")

        return output_service.download_outputs(study_id, output_id, data, tmp_export_file)

    @bp.delete(
        "/studies/{study_id}/outputs/{output_id}",
        summary="Delete a simulation output",
    )
    def delete_output(study_id: str, output_id: str) -> None:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"FDeleting output {output_id} from study {study_id}")
        output_service.delete_output(study_id, output_id)

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/_archive",
        summary="Archive output",
    )
    def archive_output(study_id: str, output_id: str) -> str | None:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Archiving of the output {output_id} of the study {study_id}")

        content = output_service.archive_output(study_id, output_id)
        return content

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/_unarchive",
        summary="Unarchive output",
    )
    def unarchive_output(study_id: str, output_id: str) -> str | None:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Unarchiving of the output {output_id} of the study {study_id}")

        content = output_service.unarchive_output(study_id, output_id)
        return content

    @bp.get(
        "/private/studies/{study_id}/outputs/{output_id}/digest-ui",
        summary="Display an output digest file for the front-end",
    )
    def get_digest_file(study_id: str, output_id: str) -> DigestUI:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_string(output_id)
        logger.info(f"Retrieving the digest file for the output {output_id} of the study {study_id}")
        return output_service.get_digest_file(study_id, output_id)

    @bp.get(
        "/studies/{study_id}/outputs",
        summary="Get global information about a study simulation result",
    )
    def sim_result(study_id: str) -> list[StudySimResultDTO]:
        logger.info(f"Fetching output list for study {study_id}")
        study_id = sanitize_uuid(study_id)
        content = output_service.get_study_sim_result(study_id)
        return content

    @bp.get(
        "/studies/{uuid}/outputs/{output_id}/aggregate/areas/mc-ind",
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
        download_expiration_time: Annotated[int, download_expiration_time_query] = DEFAULT_DOWNLOAD_EXPIRATION_TIME,
    ) -> str:
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
        - `download_expiration_time`: Expiration time for the download file (in minutes).
        - `export_format`: Returned file format (csv by default).

        Returns:
            download id
        """
        logger.info(
            f"Aggregating areas output data for study {uuid}, output {output_id},"
            f"from files '{query_file}-{frequency}.txt'"
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return output_service.create_aggregated_output_data_download(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            export_format=export_format,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(areas_ids),
            mc_years=[int(mc_year) for mc_year in _split_comma_separated_values(mc_years)],
            download_name=download_name,
            download_expiration_time_in_minutes=download_expiration_time,
            download_log=download_log,
        )

    @bp.get(
        "/studies/{uuid}/areas/aggregate/mc-ind/{output_id}",
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
    ) -> str:
        return aggregate_areas_raw_data(
            uuid, output_id, query_file, frequency, mc_years, areas_ids, columns_names, export_format
        )

    @bp.get(
        "/studies/{uuid}/outputs/{output_id}/aggregate/links/mc-ind",
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
        download_expiration_time: Annotated[int, download_expiration_time_query] = DEFAULT_DOWNLOAD_EXPIRATION_TIME,
    ) -> str:
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
        - `download_expiration_time`: Expiration time for the download file (in minutes).
        - `export_format`: Returned file format (csv by default).

        Returns:
            download id
        """
        logger.info(
            f"Aggregating links output data for study {uuid}, output {output_id},"
            f"from files '{query_file}-{frequency}.txt'"
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)
        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return output_service.create_aggregated_output_data_download(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            export_format=export_format,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(links_ids),
            mc_years=[int(mc_year) for mc_year in _split_comma_separated_values(mc_years)],
            download_name=download_name,
            download_expiration_time_in_minutes=download_expiration_time,
            download_log=download_log,
        )

    @bp.get(
        "/studies/{uuid}/links/aggregate/mc-ind/{output_id}",
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
    ) -> str:
        return aggregate_links_raw_data(
            uuid, output_id, query_file, frequency, mc_years, links_ids, columns_names, export_format
        )

    @bp.get(
        "/studies/{uuid}/outputs/{output_id}/aggregate/areas/mc-all",
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
        download_expiration_time: Annotated[int, download_expiration_time_query] = DEFAULT_DOWNLOAD_EXPIRATION_TIME,
    ) -> str:
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
        - `download_expiration_time`: Expiration time for the download file (in minutes).
        - `export_format`: Returned file format (csv by default).

        Returns:
            download id
        """
        logger.info(
            f"Aggregating areas output data for study {uuid}, output {output_id},"
            f"from files '{query_file}-{frequency}.txt'"
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return output_service.create_aggregated_output_data_download(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            export_format=export_format,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(areas_ids),
            download_name=download_name,
            download_expiration_time_in_minutes=download_expiration_time,
            download_log=download_log,
        )

    @bp.get(
        "/studies/{uuid}/areas/aggregate/mc-all/{output_id}",
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
    ) -> str:
        return aggregate_areas_raw_data__all(
            uuid, output_id, query_file, frequency, areas_ids, columns_names, export_format
        )

    @bp.get(
        "/studies/{uuid}/outputs/{output_id}/aggregate/links/mc-all",
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
        download_expiration_time: Annotated[int, download_expiration_time_query] = DEFAULT_DOWNLOAD_EXPIRATION_TIME,
    ) -> str:
        """
        Create an aggregation of links in mc-all

        Parameters:

        - `uuid`: study ID
        - `output_id`: the output ID aka the simulation ID
        - `query_file`: "values", "id"
        - `frequency`: "hourly", "daily", "weekly", "monthly", "annual"
        - `links_ids`: which links to be selected (ex: "be - fr"). If empty, all are selected (comma separated)
        - `columns_names`: names or regexes (if `query_file` is of type `details`) to select columns (comma separated)
        - `download_expiration_time`: Expiration time for the download file (in minutes).
        - `export_format`: Returned file format (csv by default).

        Returns:
            download id
        """
        logger.info(
            f"Aggregating links mc-all data for study {uuid}, output {output_id},"
            f"from files '{query_file}-{frequency}.txt'"
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = (
            f"Aggregate output '{output_id}' data for study '{uuid}' and prepares the output in a {export_format} file."
        )

        return output_service.create_aggregated_output_data_download(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            export_format=export_format,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(links_ids),
            download_name=download_name,
            download_expiration_time_in_minutes=download_expiration_time,
            download_log=download_log,
        )

    @bp.get(
        "/studies/{uuid}/links/aggregate/mc-all/{output_id}",
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
    ) -> str:
        return aggregate_links_raw_data__all(
            uuid, output_id, query_file, frequency, links_ids, columns_names, export_format
        )

    @bp.get(
        "/studies/{uuid}/output/{output_id}/variables-list",
        summary="Retrieves the list of variables for a given output",
    )
    def get_output_variables_list(uuid: str, output_id: str) -> OutputVariablesList:
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)
        return output_service.get_output_variables_list(uuid, output_id)

    @bp.get(
        "/studies/{uuid}/output/{output_id}/variables-views/data",
        summary="Fetches the variables view for a given output and a given configuration",
        responses={
            404: {"model": OutputVariablesViewResponse},
            200: {"data": [[4], [5]], "columns": [0, 1]},
        },
    )
    def get_output_variables_view(
        uuid: str,
        output_id: str,
        variable_name: str,
        frequency: MatrixFrequency,
        type: OutputVariablesType,
        area_id: str | None = None,
        area_from_id: str | None = None,
        area_to_id: str | None = None,
        thermal_id: str | None = None,
        renewable_id: str | None = None,
        st_storage_id: str | None = None,
    ) -> Response:
        """
        Fetches the variables view for a given output and a given configuration.
        If the view does not exist in DB yet, returns an HTTP 404 response.
        The user will have to use the endpoint `POST /variables-views/materialize` with the same configuration first.
        """
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        item_id = _to_item_id(
            type=type,
            area_id=area_id,
            area_from_id=area_from_id,
            area_to_id=area_to_id,
            thermal_id=thermal_id,
            renewable_id=renewable_id,
            st_storage_id=st_storage_id,
        )
        view = output_service.get_output_variables_view(uuid, output_id, item_id, variable_name, frequency)
        if isinstance(view, pd.DataFrame):
            content = view.to_dict(orient="split", index=False)
            return Response(content=to_json(content), media_type="application/json")
        return Response(status_code=404, content=to_json(view), media_type="application/json")

    @bp.get(
        "/studies/{uuid}/output/{output_id}/variables-views/export",
        summary="Export the variables view for a given output and a given configuration in a given format",
    )
    def export_output_variables_view(
        uuid: str,
        output_id: str,
        variable_name: str,
        frequency: MatrixFrequency,
        type: OutputVariablesType,
        area_id: str | None = None,
        area_from_id: str | None = None,
        area_to_id: str | None = None,
        thermal_id: str | None = None,
        renewable_id: str | None = None,
        st_storage_id: str | None = None,
        export_format: TableExportFormat = TableExportFormat.CSV,
        with_header: bool = Query(
            True, alias="header", description="Whether to include the header or not", title="With Header"
        ),
        with_index: bool = Query(
            True, alias="index", description="Whether to include the index or not", title="With Index"
        ),
    ) -> Response:
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        item_id = _to_item_id(
            type=type,
            area_id=area_id,
            area_from_id=area_from_id,
            area_to_id=area_to_id,
            thermal_id=thermal_id,
            renewable_id=renewable_id,
            st_storage_id=st_storage_id,
        )
        view = output_service.get_output_variables_view(uuid, output_id, item_id, variable_name, frequency, with_index)
        if not isinstance(view, pd.DataFrame):
            return Response(status_code=HTTPStatus.NOT_FOUND, content=to_json(view), media_type="application/json")

        buffer = BytesIO()
        export_format.export_table(view, buffer, with_header=with_header, with_index=with_index)
        return Response(status_code=HTTPStatus.OK, content=buffer.getvalue(), media_type=export_format.media_type)

    @bp.post(
        "/studies/{uuid}/output/{output_id}/variables-views/materialize",
        summary="Materialize the variables view for a given output and a given configuration",
    )
    def materialize_output_variables_view(
        uuid: str,
        output_id: str,
        variable_name: str,
        frequency: MatrixFrequency,
        type: OutputVariablesType,
        area_id: str | None = None,
        area_from_id: str | None = None,
        area_to_id: str | None = None,
        thermal_id: str | None = None,
        renewable_id: str | None = None,
        st_storage_id: str | None = None,
    ) -> str:
        """
        Materializes a variables view for a given output and a given configuration.
        If the view is already registered in DB, raise an HTTP Conflict error.
        The user should use the endpoint `GET /variables-views/data` with the same configuration.
        """
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)
        item_id = _to_item_id(
            type=type,
            area_id=area_id,
            area_from_id=area_from_id,
            area_to_id=area_to_id,
            thermal_id=thermal_id,
            renewable_id=renewable_id,
            st_storage_id=st_storage_id,
        )
        return output_service.materialize_output_variables_view(
            uuid,
            output_id,
            item_id,
            variable_name,
            frequency,
        )

    return bp
