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
import http
import io
import logging
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, List, Sequence

from fastapi import APIRouter, Body, Depends, File, HTTPException
from fastapi.params import Query
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.model import SUB_JSON
from antarest.core.requests import RequestParameters
from antarest.core.serde.json import from_json, to_json
from antarest.core.swagger import get_path_examples
from antarest.core.utils.utils import sanitize_string, sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.business.aggregator_management import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
)
from antarest.study.service import StudyService
from antarest.study.storage.df_download import TableExportFormat, export_file
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.variantstudy.model.command.create_user_resource import ResourceType

logger = logging.getLogger(__name__)


# noinspection SpellCheckingInspection

CONTENT_TYPES = {
    # (Portable Document Format)
    ".pdf": ("application/pdf", None),
    # (Microsoft Excel)
    ".xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", None),
    # (Microsoft Word)
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", None),
    # (Microsoft PowerPoint)
    ".pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", None),
    # (LibreOffice Writer)
    ".odt": ("application/vnd.oasis.opendocument.text", None),
    # (LibreOffice Calc)
    ".ods": ("application/vnd.oasis.opendocument.spreadsheet", None),
    # (LibreOffice Impress)
    ".odp": ("application/vnd.oasis.opendocument.presentation", None),
    # (Comma-Separated Values)
    ".csv": ("text/csv", "utf-8"),
    # (Tab-Separated Values)
    ".tsv": ("text/tab-separated-values", "utf-8"),
    # (Plain Text)
    ".txt": ("text/plain", "utf-8"),
    # (JSON)
    ".json": ("application/json", "utf-8"),
    # (INI FILE)
    ".ini": ("text/plain", "utf-8"),
    # (antares file)
    ".antares": ("text/plain", "utf-8"),
}

DEFAULT_EXPORT_FORMAT = Query(TableExportFormat.CSV, alias="format", description="Export format", title="Export Format")
PATH_TYPE = Annotated[str, Query(openapi_examples=get_path_examples())]


def _split_comma_separated_values(value: str, *, default: Sequence[str] = ()) -> Sequence[str]:
    """Split a comma-separated list of values into an ordered set of strings."""
    values = value.split(",") if value else default
    # drop whitespace around values
    values = [v.strip() for v in values]
    # remove duplicates and preserve order (to have a deterministic result for unit tests).
    return list(collections.OrderedDict.fromkeys(values))


def create_raw_study_routes(
    study_service: StudyService,
    config: Config,
) -> APIRouter:
    """
    Endpoint implementation for studies management
    Args:
        study_service: study service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get(
        "/studies/{uuid}/raw",
        tags=[APITag.study_raw_data],
        summary="Retrieve Raw Data from Study: JSON, Text, or File Attachment",
    )
    def get_study_data(
        uuid: str,
        path: PATH_TYPE = "/",
        depth: int = 3,
        formatted: bool = True,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        """
        Fetches raw data from a study, and returns the data
        in different formats based on the file type, or as a JSON response.

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the data to fetch.
        - `depth`: The depth of the data to retrieve.
        - `formatted`: A flag specifying whether the data should be returned in a formatted manner.

        Returns the fetched data: a JSON object (in most cases), a plain text file
        or a file attachment (Microsoft Office document, TSV/TSV file...).
        """
        logger.info(
            f"📘 Fetching data at {path} (depth={depth}) from study {uuid}",
            extra={"user": current_user.id},
        )
        parameters = RequestParameters(user=current_user)
        output = study_service.get(uuid, path, depth=depth, formatted=formatted, params=parameters)

        if isinstance(output, bytes):
            # Guess the suffix form the target data
            resource_path = PurePosixPath(path)
            parent_cfg = study_service.get(uuid, str(resource_path.parent), depth=2, formatted=True, params=parameters)
            child = parent_cfg[resource_path.name]
            suffix = PurePosixPath(child).suffix

            content_type, encoding = CONTENT_TYPES.get(suffix, (None, None))
            if content_type == "application/json":
                # Use `JSONResponse` to ensure to return a valid JSON response
                # that checks `NaN` and `Infinity` values.
                try:
                    output = from_json(output)
                    return JSONResponse(content=output)
                except ValueError as exc:
                    raise HTTPException(
                        status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
                        detail=f"Invalid JSON configuration in path '{path}': {exc}",
                    ) from None
            elif encoding:
                try:
                    response = PlainTextResponse(output, media_type=content_type)
                    response.charset = encoding
                    return response

                except ValueError as exc:
                    raise HTTPException(
                        status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY,
                        detail=f"Invalid plain text configuration in path '{path}': {exc}",
                    ) from None
            elif content_type:
                headers = {"Content-Disposition": f"attachment; filename={resource_path.name}"}
                return StreamingResponse(
                    io.BytesIO(output),
                    media_type=content_type,
                    headers=headers,
                )
            else:
                # Unknown content types are considered binary,
                # because it's better to avoid raising an exception.
                return Response(content=output, media_type="application/octet-stream")

        # We want to allow `NaN`, `+Infinity`, and `-Infinity` values in the JSON response
        # even though they are not standard JSON values because they are supported in JavaScript.
        # Additionally, we cannot use `orjson` because, despite its superior performance, it converts
        # `NaN` and other values to `null`, even when using a custom encoder.
        json_response = to_json(output)
        return Response(content=json_response, media_type="application/json")

    @bp.get(
        "/studies/{uuid}/raw/original-file",
        tags=[APITag.study_raw_data],
        summary="Retrieve Raw file from a Study folder in its original format",
    )
    def get_study_file(
        uuid: str,
        path: PATH_TYPE = "/",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        """
        Fetches for a file in its original format from a study folder

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the file to fetch.

        Returns the fetched file in its original format.
        """
        logger.info(
            f"📘 Fetching file at {path} from study {uuid}",
            extra={"user": current_user.id},
        )
        parameters = RequestParameters(user=current_user)
        original_file = study_service.get_file(uuid, path, params=parameters)
        filename = original_file.filename
        output = original_file.content
        suffix = original_file.suffix
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
        }

        # Guess the suffix form the filename suffix
        content_type, _ = CONTENT_TYPES.get(suffix, (None, None))
        media_type = content_type or "application/octet-stream"
        return Response(content=output, media_type=media_type, headers=headers)

    @bp.delete(
        "/studies/{uuid}/raw",
        tags=[APITag.study_raw_data],
        summary="Delete files or folders located inside the 'User' folder",
        response_model=None,
    )
    def delete_file(
        uuid: str,
        path: Annotated[
            str,
            Query(
                openapi_examples={
                    "user/wind_solar/synthesis_windSolar.xlsx": {"value": "user/wind_solar/synthesis_windSolar.xlsx"}
                },
            ),
        ] = "/",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        uuid = sanitize_uuid(uuid)
        logger.info(f"Deleting path {path} inside study {uuid}", extra={"user": current_user.id})
        study_service.delete_user_file_or_folder(uuid, path, current_user)

    @bp.get(
        "/studies/{uuid}/areas/aggregate/mc-ind/{output_id}",
        tags=[APITag.study_raw_data],
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
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,  # type: ignore
        current_user: JWTUser = Depends(auth.get_current_user),
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
            f"from files '{query_file}-{frequency}.txt'",
            extra={"user": current_user.id},
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        parameters = RequestParameters(user=current_user)
        df_matrix = study_service.aggregate_output_data(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(areas_ids),
            params=parameters,
            mc_years=[int(mc_year) for mc_year in _split_comma_separated_values(mc_years)],
        )

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return export_file(
            df_matrix,
            study_service.file_transfer_manager,
            export_format,
            False,
            True,
            download_name,
            download_log,
            current_user,
        )

    @bp.get(
        "/studies/{uuid}/links/aggregate/mc-ind/{output_id}",
        tags=[APITag.study_raw_data],
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
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,  # type: ignore
        current_user: JWTUser = Depends(auth.get_current_user),
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
            f"from files '{query_file}-{frequency}.txt'",
            extra={"user": current_user.id},
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        parameters = RequestParameters(user=current_user)
        df_matrix = study_service.aggregate_output_data(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(links_ids),
            params=parameters,
            mc_years=[int(mc_year) for mc_year in _split_comma_separated_values(mc_years)],
        )

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return export_file(
            df_matrix,
            study_service.file_transfer_manager,
            export_format,
            False,
            True,
            download_name,
            download_log,
            current_user,
        )

    @bp.get(
        "/studies/{uuid}/areas/aggregate/mc-all/{output_id}",
        tags=[APITag.study_raw_data],
        summary="Retrieve Aggregated Areas Raw Data from Study Economy MCs All Outputs",
    )
    def aggregate_areas_raw_data__all(
        uuid: str,
        output_id: str,
        query_file: MCAllAreasQueryFile,
        frequency: MatrixFrequency,
        areas_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,  # type: ignore
        current_user: JWTUser = Depends(auth.get_current_user),
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
            f"from files '{query_file}-{frequency}.txt'",
            extra={"user": current_user.id},
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        parameters = RequestParameters(user=current_user)
        df_matrix = study_service.aggregate_output_data(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(areas_ids),
            params=parameters,
        )

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return export_file(
            df_matrix,
            study_service.file_transfer_manager,
            export_format,
            False,
            True,
            download_name,
            download_log,
            current_user,
        )

    @bp.get(
        "/studies/{uuid}/links/aggregate/mc-all/{output_id}",
        tags=[APITag.study_raw_data],
        summary="Retrieve Aggregated Links Raw Data from Study Economy MC-All Outputs",
    )
    def aggregate_links_raw_data__all(
        uuid: str,
        output_id: str,
        query_file: MCAllLinksQueryFile,
        frequency: MatrixFrequency,
        links_ids: str = "",
        columns_names: str = "",
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,  # type: ignore
        current_user: JWTUser = Depends(auth.get_current_user),
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
            f"from files '{query_file}-{frequency}.txt'",
            extra={"user": current_user.id},
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        output_id = sanitize_string(output_id)

        parameters = RequestParameters(user=current_user)
        df_matrix = study_service.aggregate_output_data(
            uuid,
            output_id=output_id,
            query_file=query_file,
            frequency=frequency,
            columns_names=_split_comma_separated_values(columns_names),
            ids_to_consider=_split_comma_separated_values(links_ids),
            params=parameters,
        )

        download_name = f"aggregated_output_{uuid}_{output_id}{export_format.suffix}"
        download_log = f"Exporting aggregated output data for study '{uuid}' as {export_format} file"

        return export_file(
            df_matrix,
            study_service.file_transfer_manager,
            export_format,
            False,
            True,
            download_name,
            download_log,
            current_user,
        )

    @bp.post(
        "/studies/{uuid}/raw",
        status_code=http.HTTPStatus.OK,
        tags=[APITag.study_raw_data],
        summary="Update study by posting formatted data",
    )
    def edit_study(
        uuid: str,
        path: PATH_TYPE = "/",
        data: SUB_JSON = Body(default=""),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        """
        Updates raw data for a study by posting formatted data.

        > NOTE: use the PUT endpoint to upload a file.

        Parameters:

        - `uuid`: The UUID of the study.
        - `path`: The path to the data to update. Defaults to "/".
        - `data`: The formatted data to be posted. Could be a JSON object, or a string. Defaults to an empty string.

        """
        logger.info(f"Editing data at {path} for study {uuid}", extra={"user": current_user.id})
        path = sanitize_string(path)
        params = RequestParameters(user=current_user)
        return study_service.edit_study(uuid, path, data, params)

    @bp.put(
        "/studies/{uuid}/raw",
        status_code=http.HTTPStatus.NO_CONTENT,
        tags=[APITag.study_raw_data],
        summary="Update data by posting a Raw file",
    )
    def replace_study_file(
        uuid: str,
        path: PATH_TYPE = "/",
        file: bytes = File(default=None),
        create_missing: bool = Query(
            False,
            description="Create file or parent directories if missing.",
        ),  # type: ignore
        resource_type: ResourceType = ResourceType.FILE,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Update raw data for a study by posting a raw file.

        Parameters:

        - `uuid`: The UUID of the study.
        - `path`: The path to the data to update. Defaults to "/".
        - `file`: The raw file to be posted (e.g. a CSV file opened in binary mode).
        - `create_missing`: Flag to indicate whether to create file and parent directories if missing.
        - `resource_type`: When set to "folder" and `create_missing` is True, creates a folder. Else (default value), it's ignored.

        """
        if file is not None and resource_type == ResourceType.FOLDER:
            raise HTTPException(status_code=422, detail="Argument mismatch: Cannot give a content to create a folder")
        if file is None and resource_type == ResourceType.FILE:
            raise HTTPException(status_code=422, detail="Argument mismatch: Must give a content to create a file")

        path = sanitize_string(path)
        params = RequestParameters(user=current_user)
        if resource_type == ResourceType.FOLDER and create_missing:  # type: ignore
            logger.info(f"Creating folder {path} for study {uuid}", extra={"user": current_user.id})
            study_service.create_user_folder(uuid, path, current_user)
        else:
            logger.info(f"Uploading new data file at {path} for study {uuid}", extra={"user": current_user.id})
            study_service.edit_study(uuid, path, file, params, create_missing=create_missing)

    @bp.get(
        "/studies/{uuid}/raw/validate",
        summary="Launch test validation on study",
        tags=[APITag.study_raw_data],
        response_model=List[str],
    )
    def validate(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[str]:
        """
        Launches test validation on the raw data of a study.
        The validation is done recursively on all the files in the study

        Parameters:
        - `uuid`: The UUID of the study.

        Response:
        - A list of strings indicating validation errors (if any) for the study's raw data.
          The list is empty if no errors were found.
        """
        logger.info(
            f"Validating data for study {uuid}",
            extra={"user": current_user.id},
        )
        return study_service.check_errors(uuid)

    @bp.get(
        "/studies/{uuid}/raw/download",
        summary="Download a matrix in a given format",
        tags=[APITag.study_raw_data],
    )
    def get_matrix(
        uuid: str,
        matrix_path: str = Query(  # type: ignore
            ..., alias="path", description="Relative path of the matrix to download", title="Matrix Path"
        ),
        export_format: TableExportFormat = DEFAULT_EXPORT_FORMAT,  # type: ignore
        with_header: bool = Query(  # type: ignore
            True, alias="header", description="Whether to include the header or not", title="With Header"
        ),
        with_index: bool = Query(  # type: ignore
            True, alias="index", description="Whether to include the index or not", title="With Index"
        ),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> FileResponse:
        """
        Download a matrix in a given format.

        Parameters:

        - `uuid`: study ID
        - `matrix_path`: Relative path of the matrix to download.
        - `export_format`: Returned file format (csv by default).
        - `with_header`:  Whether to include the header or not.
        - `with_index`: Whether to include the index or not.

        Returns:
            FileResponse that corresponds to the matrix file in the requested format.
        """
        logger.info(
            f"Exporting matrix '{matrix_path}' to {export_format} format for study '{uuid}'",
            extra={"user": current_user.id},
        )

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        matrix_path = sanitize_string(matrix_path)

        parameters = RequestParameters(user=current_user)
        df_matrix = study_service.get_matrix_with_index_and_header(
            study_id=uuid,
            path=matrix_path,
            with_index=with_index,
            with_header=with_header,
            parameters=parameters,
        )

        matrix_name = Path(matrix_path).stem
        download_name = f"{matrix_name}{export_format.suffix}"
        download_log = f"Exporting matrix '{matrix_name}' to {export_format} format for study '{uuid}'"

        return export_file(
            df_matrix,
            study_service.file_transfer_manager,
            export_format,
            with_index,
            with_header,
            download_name,
            download_log,
            current_user,
        )

    return bp
