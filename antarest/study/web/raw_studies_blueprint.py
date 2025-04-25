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

import http
import io
import logging
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, List

from fastapi import APIRouter, Body, Depends, File, HTTPException
from fastapi.params import Query
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse

from antarest.core.config import Config
from antarest.core.model import SUB_JSON
from antarest.core.serde.json import from_json, to_json
from antarest.core.swagger import get_path_examples
from antarest.core.utils.utils import sanitize_string, sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.service import StudyService
from antarest.study.storage.df_download import TableExportFormat, export_file
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
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", dependencies=[Depends(auth.yield_current_user)])

    @bp.get(
        "/studies/{uuid}/raw",
        tags=[APITag.study_raw_data],
        summary="Retrieve Raw Data from Study: JSON, Text, or File Attachment",
    )
    def get_study_data(uuid: str, path: PATH_TYPE = "/", depth: int = 3, formatted: bool = True) -> Any:
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
        logger.info(f"📘 Fetching data at {path} (depth={depth}) from study {uuid}")
        output = study_service.get(uuid, path, depth=depth, formatted=formatted)

        if isinstance(output, bytes):
            # Guess the suffix form the target data
            resource_path = PurePosixPath(path)
            parent_cfg = study_service.get(uuid, str(resource_path.parent), depth=2, formatted=True)
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
    def get_study_file(uuid: str, path: PATH_TYPE = "/") -> Any:
        """
        Fetches for a file in its original format from a study folder

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the file to fetch.

        Returns the fetched file in its original format.
        """
        logger.info(f"📘 Fetching file at {path} from study {uuid}")
        original_file = study_service.get_file(uuid, path)
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
    ) -> Any:
        uuid = sanitize_uuid(uuid)
        logger.info(f"Deleting path {path} inside study {uuid}")
        study_service.delete_user_file_or_folder(uuid, path)

    @bp.post(
        "/studies/{uuid}/raw",
        status_code=http.HTTPStatus.OK,
        tags=[APITag.study_raw_data],
        summary="Update study by posting formatted data",
    )
    def edit_study(uuid: str, path: PATH_TYPE = "/", data: SUB_JSON = Body(default="")) -> Any:
        """
        Updates raw data for a study by posting formatted data.

        > NOTE: use the PUT endpoint to upload a file.

        Parameters:

        - `uuid`: The UUID of the study.
        - `path`: The path to the data to update. Defaults to "/".
        - `data`: The formatted data to be posted. Could be a JSON object, or a string. Defaults to an empty string.

        """
        logger.info(f"Editing data at {path} for study {uuid}")
        path = sanitize_string(path)
        return study_service.edit_study(uuid, path, data)

    @bp.put(
        "/studies/{uuid}/raw",
        status_code=http.HTTPStatus.NO_CONTENT,
        tags=[APITag.study_raw_data],
        summary="Update data by posting a Raw file or by creating folder(s)",
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
    ) -> None:
        """
        Update raw data for a study by posting a raw file or by creating folder(s).

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
        if resource_type == ResourceType.FOLDER and create_missing:  # type: ignore
            logger.info(f"Creating folder {path} for study {uuid}")
            study_service.create_user_folder(uuid, path)
        else:
            logger.info(f"Uploading new data file at {path} for study {uuid}")
            study_service.edit_study(uuid, path, file, create_missing=create_missing)

    @bp.get(
        "/studies/{uuid}/raw/validate",
        summary="Launch test validation on study",
        tags=[APITag.study_raw_data],
        response_model=List[str],
    )
    def validate(uuid: str) -> List[str]:
        """
        Launches test validation on the raw data of a study.
        The validation is done recursively on all the files in the study

        Parameters:
        - `uuid`: The UUID of the study.

        Response:
        - A list of strings indicating validation errors (if any) for the study's raw data.
          The list is empty if no errors were found.
        """
        logger.info(f"Validating data for study {uuid}")
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
        logger.info(f"Exporting matrix '{matrix_path}' to {export_format} format for study '{uuid}'")

        # Avoid vulnerabilities by sanitizing the `uuid` and `output_id` parameters
        uuid = sanitize_uuid(uuid)
        matrix_path = sanitize_string(matrix_path)

        df_matrix = study_service.get_matrix_with_index_and_header(
            study_id=uuid, path=matrix_path, with_index=with_index, with_header=with_header
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
        )

    return bp
