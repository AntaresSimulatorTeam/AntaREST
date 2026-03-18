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

import http
import io
import logging
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal, TypeAlias

import polars as pl
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Body, Depends, File, HTTPException
from fastapi.openapi.models import Example
from fastapi.params import Query
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse

from antarest.core.api_types import SanitizedStr, UuidStr
from antarest.core.exceptions import IncorrectPathError
from antarest.core.model import SUB_JSON
from antarest.core.serde.json import from_json, to_json
from antarest.core.serde.matrix_export import TableExportFormat, simplify_dataframe
from antarest.core.utils.utils import sanitize_string
from antarest.core.utils.web import APITag
from antarest.dependencies import StudyServiceDep, auth_required
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.model.user_model import ResourceType
from antarest.study.storage.df_download import export_file

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

ExportFormatQuery: TypeAlias = Annotated[
    TableExportFormat, Query(alias="format", description="Export format", title="Export Format")
]

_sim = "{sim} = simulation index <br/>"
_area = "{area} = area name to select <br/>"
_link = "{link} = link name to select <br/>"
_attachment = "User-defined file attachment <br/>"

# noinspection SpellCheckingInspection
_path_examples: list[tuple[str, str]] = [
    ("layers/layers", ""),
    ("settings/generaldata", ""),
    ("output/{sim}/about-the-study/parameters", _sim),
    ("output/{sim}/about-the-study/study", _sim),
    ("output/{sim}/info(.antares-output)", _sim),
    ("input/areas/{area}/optimization", _area),
    ("input/areas/{area}/ui", _area),
    ("input/bindingconstraints/bindingconstraints", ""),
    ("input/hydro/hydro", ""),
    ("input/links/{area}/properties/{link}", _area + _link),
    ("input/load/prepro/{area}/settings", _area),
    ("input/solar/prepro/{area}/settings", _area),
    ("input/thermal/clusters/{area}/list", _area),
    ("input/thermal/areas", ""),
    ("input/wind/prepro/{area}/settings", _area),
    ("user/wind_solar/synthesis_windSolar.xlsx", _attachment),
]


def _get_path_examples() -> dict[str, Example]:
    return {url: {"value": url, "description": des} for url, des in _path_examples}


PATH_TYPE = Annotated[SanitizedStr, Query(openapi_examples=_get_path_examples())]


class MatrixFormat(EnumIgnoreCase):
    JSON = "json"
    ARROW_COMPRESSED = "arrow compressed"
    ARROW_UNCOMPRESSED = "arrow uncompressed"
    PLAIN = "plain"

    def serialize_dataframe(self, dataframe: pl.DataFrame) -> Response:
        polars_type: type[pl.Int32] | type[pl.Int64] = pl.Int64
        # For textual formats, int64 and int32 are represented in the same way, so we use int64 to catch bigger numbers.
        # For the arrow format, on the other hand, the size of an int32 is half the size of an int64 so we prefer int32.
        if self in {MatrixFormat.ARROW_COMPRESSED, MatrixFormat.ARROW_UNCOMPRESSED}:
            polars_type = pl.Int32
        dataframe = simplify_dataframe(dataframe, polars_type)

        if self == MatrixFormat.PLAIN:
            if dataframe.is_empty():
                return Response(content=b"", media_type="application/octet-stream")
            string_buffer = io.StringIO()
            dataframe.write_csv(string_buffer, separator="\t", include_header=False)
            return Response(content=string_buffer.getvalue(), media_type="text/csv")

        buffer = io.BytesIO()
        if self == MatrixFormat.JSON:
            # We have to do `to_json(DataFrame.to_dict())` to keep the NaNs for backward compatibility.
            # The method DataFrame.to_json() is faster but use null instead of NaNs.
            content = to_json(dataframe.to_pandas().to_dict(orient="split"))
            return Response(content=content, media_type="application/json")

        else:
            compression_mapping: dict[MatrixFormat, Literal["zstd", "uncompressed"]] = {
                MatrixFormat.ARROW_COMPRESSED: "zstd",
                MatrixFormat.ARROW_UNCOMPRESSED: "uncompressed",
            }
            dataframe.write_ipc(buffer, compression=compression_mapping[self])
            return Response(content=buffer.getvalue(), media_type="application/vnd.apache.arrow.file")


def create_raw_study_routes() -> APIRouter:
    """
    Endpoint implementation for studies management
    """
    bp = APIRouter(
        prefix="/v1", tags=[APITag.study_raw_data], dependencies=[Depends(auth_required)], route_class=DishkaRoute
    )

    @bp.get(
        "/studies/{uuid}/raw",
        summary="Retrieve Raw Data from Study: JSON, Text, or File Attachment",
    )
    def get_study_data(
        study_service: StudyServiceDep,
        uuid: UuidStr,
        path: PATH_TYPE = "/",
        depth: int = 3,
        formatted: bool = True,
        matrix_format: MatrixFormat | None = None,
    ) -> Response:
        """
        Fetches raw data from a study, and returns the data
        in different formats based on the file type, or as a JSON response.

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the data to fetch.
        - `depth`: The depth of the data to retrieve.
        - `formatted`: Flag used to retrieve data from files which aren't matrices.
        - `matrix_format`: An enum specifying the format in which the matrix should be returned.

        Returns the fetched data: a JSON object (in most cases), a plain text file
        or a file attachment (Microsoft Office document, TSV/TSV file...).
        """
        logger.info(f"📘 Fetching data at {path} (depth={depth}) from study {uuid}")

        output = study_service.get_raw_content(uuid, path, depth, formatted)

        if isinstance(output, pl.DataFrame):
            if matrix_format is None:
                matrix_format = MatrixFormat.JSON if formatted else MatrixFormat.PLAIN
            return matrix_format.serialize_dataframe(output)

        if matrix_format in {MatrixFormat.ARROW_COMPRESSED, MatrixFormat.ARROW_UNCOMPRESSED}:
            # The user asked for a format only supported for matrices.
            raise IncorrectPathError(f"The provided path does not point to a valid matrix: '{path}'")

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
        summary="Retrieve Raw file from a Study folder in its original format",
    )
    def get_study_file(study_service: StudyServiceDep, uuid: UuidStr, path: PATH_TYPE = "/") -> Response:
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
        summary="Delete files or folders located inside the 'User' folder",
    )
    def delete_file(
        study_service: StudyServiceDep,
        uuid: UuidStr,
        path: Annotated[
            SanitizedStr,
            Query(
                openapi_examples={
                    "user/wind_solar/synthesis_windSolar.xlsx": {"value": "user/wind_solar/synthesis_windSolar.xlsx"}
                },
            ),
        ] = "/",
    ) -> None:
        logger.info(f"Deleting path {path} inside study {uuid}")
        study_service.delete_user_file_or_folder(uuid, path)

    @bp.post(
        "/studies/{uuid}/raw",
        status_code=http.HTTPStatus.OK,
        summary="Update study by posting formatted data",
    )
    def edit_study(
        study_service: StudyServiceDep,
        uuid: UuidStr,
        path: PATH_TYPE = "/",
        data: Annotated[SUB_JSON, Body()] = "",
    ) -> Any:
        """
        Same endpoint as the PUT one.
        Only difference is that it cannot create an empty folder.
        """
        logger.info(f"Editing data at {path} for study {uuid}")
        path = sanitize_string(path)
        return study_service.edit_study(uuid, path, data)

    @bp.put(
        "/studies/{uuid}/raw",
        status_code=http.HTTPStatus.NO_CONTENT,
        summary="Update data by posting a Raw file or by creating folder(s)",
    )
    def replace_study_file(
        study_service: StudyServiceDep,
        uuid: UuidStr,
        path: PATH_TYPE = "/",
        file: Annotated[bytes | None, File()] = None,
        create_missing: Annotated[bool, Query(deprecated=True)] = True,
        resource_type: ResourceType = ResourceType.FILE,
    ) -> None:
        """
        Update raw data for a study by posting a raw file or by creating folder(s).

        Parameters:

        - `uuid`: The UUID of the study.
        - `path`: The path to the data to update. Defaults to "/".
        - `file`: The raw file to be posted (e.g. a CSV file opened in binary mode).
        - `resource_type`: When set to "folder", creates a folder. Else (default value), it's ignored.

        """
        if file is not None and resource_type == ResourceType.FOLDER:
            raise HTTPException(status_code=422, detail="Argument mismatch: Cannot give a content to create a folder")
        if file is None and resource_type == ResourceType.FILE:
            raise HTTPException(status_code=422, detail="Argument mismatch: Must give a content to create a file")

        path = sanitize_string(path)
        if resource_type == ResourceType.FOLDER:
            logger.info(f"Creating folder {path} for study {uuid}")
            study_service.create_user_folder(uuid, path)
        else:
            logger.info(f"Uploading new data file at {path} for study {uuid}")
            study_service.edit_study(uuid, path, file)

    @bp.get(
        "/studies/{uuid}/raw/download",
        summary="Download a matrix in a given format",
    )
    def get_matrix(
        study_service: StudyServiceDep,
        uuid: UuidStr,
        matrix_path: Annotated[
            SanitizedStr,
            Query(alias="path", description="Relative path of the matrix to download", title="Matrix Path"),
        ],
        export_format: ExportFormatQuery = TableExportFormat.CSV,
        with_header: Annotated[
            bool, Query(alias="header", description="Whether to include the header or not", title="With Header")
        ] = True,
        with_index: Annotated[
            bool, Query(alias="index", description="Whether to include the index or not", title="With Index")
        ] = True,
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
