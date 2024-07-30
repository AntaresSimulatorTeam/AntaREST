import collections
import http
import io
import json
import logging
import typing as t
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, Body, Depends, File, HTTPException
from fastapi.params import Param, Query
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.model import SUB_JSON
from antarest.core.requests import RequestParameters
from antarest.core.swagger import get_path_examples
from antarest.core.utils.utils import sanitize_string, sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.business.aggregator_management import AreasQueryFile, LinksQueryFile
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.service import StudyService
from antarest.study.storage.df_download import TableExportFormat, export_file
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency

try:
    import tables  # type: ignore
    import xlsxwriter  # type: ignore
except ImportError:
    raise ImportError("The 'xlsxwriter' and 'tables' packages are required") from None

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
}


class MatrixFormat(EnumIgnoreCase):
    JSON = "json"
    ARROW = "arrow"


DEFAULT_EXPORT_FORMAT = Query(TableExportFormat.CSV, alias="format", description="Export format", title="Export Format")


def _split_comma_separated_values(value: str, *, default: t.Sequence[str] = ()) -> t.Sequence[str]:
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
    def get_study(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        depth: int = 3,
        formatted: bool = True,
        format: t.Optional[MatrixFormat] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Response:
        """
        Fetches raw data from a study, and returns the data
        in different formats based on the file type, or as a JSON response.

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the data to fetch.
        - `depth`: The depth of the data to retrieve.
        - `formatted`: If false, returns the file as bytes. Else, the `format` flag applies.
        - `format`: Either 'json' or 'arrow'. Arrow format is only supported by matrix files.

        Returns the fetched data: a JSON object (in most cases), a plain text file, a matrix file in arrow format
        or a file attachment (Microsoft Office document, TSV/TSV file...).
        """
        logger.info(
            f"📘 Fetching data at {path} (depth={depth}) from study {uuid}",
            extra={"user": current_user.id},
        )
        parameters = RequestParameters(user=current_user)

        _format = format or MatrixFormat.JSON
        real_format = _format.value if formatted else None

        output = study_service.get(uuid, path, depth=depth, params=parameters, format=real_format)

        if isinstance(output, bytes):
            if real_format == MatrixFormat.ARROW:
                return Response(content=output, media_type="application/vnd.apache.arrow.file")

            # Guess the suffix form the target data
            resource_path = PurePosixPath(path)
            parent_cfg = study_service.get(
                uuid, str(resource_path.parent), depth=2, params=parameters, format=real_format
            )
            child = parent_cfg[resource_path.name]
            suffix = PurePosixPath(child).suffix

            content_type, encoding = CONTENT_TYPES.get(suffix, (None, None))
            if content_type == "application/json":
                # Use `JSONResponse` to ensure to return a valid JSON response
                # that checks `NaN` and `Infinity` values.
                try:
                    output = json.loads(output)
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
        json_response = json.dumps(
            output,
            ensure_ascii=False,
            allow_nan=True,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")
        return Response(content=json_response, media_type="application/json")

    @bp.get(
        "/studies/{uuid}/areas/aggregate/{output_id}",
        tags=[APITag.study_raw_data],
        summary="Retrieve Aggregated Areas Raw Data from Study Output",
    )
    def aggregate_areas_raw_data(
        uuid: str,
        output_id: str,
        query_file: AreasQueryFile,
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
        - `columns_names`: which columns to be selected. If empty, all are selected (comma separated)
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
            mc_years=[int(mc_year) for mc_year in _split_comma_separated_values(mc_years)],
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
            True,
            True,
            download_name,
            download_log,
            current_user,
        )

    @bp.get(
        "/studies/{uuid}/links/aggregate/{output_id}",
        tags=[APITag.study_raw_data],
        summary="Retrieve Aggregated Links Raw Data from Study Output",
    )
    def aggregate_links_raw_data(
        uuid: str,
        output_id: str,
        query_file: LinksQueryFile,
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
        - `columns_names`: which columns to be selected. If empty, all are selected (comma separated)
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
            mc_years=[int(mc_year) for mc_year in _split_comma_separated_values(mc_years)],
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
            True,
            True,
            download_name,
            download_log,
            current_user,
        )

    @bp.post(
        "/studies/{uuid}/raw",
        status_code=http.HTTPStatus.NO_CONTENT,
        tags=[APITag.study_raw_data],
        summary="Update data by posting formatted data",
    )
    def edit_study(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        data: SUB_JSON = Body(default=""),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Updates raw data for a study by posting formatted data.

        > NOTE: use the PUT endpoint to upload a file.

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the data to update. Defaults to "/".
        - `data`: The formatted data to be posted. Defaults to an empty string.
          The data could be a JSON object, or a simple string.
        """
        logger.info(
            f"Editing data at {path} for study {uuid}",
            extra={"user": current_user.id},
        )
        path = sanitize_string(path)
        params = RequestParameters(user=current_user)
        study_service.edit_study(uuid, path, data, params)

    @bp.put(
        "/studies/{uuid}/raw",
        status_code=http.HTTPStatus.NO_CONTENT,
        tags=[APITag.study_raw_data],
        summary="Update data by posting a Raw file",
    )
    def replace_study_file(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        file: bytes = File(...),
        create_missing: bool = Query(
            False,
            description="Create file or parent directories if missing.",
        ),  # type: ignore
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Update raw data for a study by posting a raw file.

        Parameters:
        - `uuid`: The UUID of the study.
        - `path`: The path to the data to update. Defaults to "/".
        - `file`: The raw file to be posted (e.g. a CSV file opened in binary mode or a matrix in arrow format).
        - `create_missing`: Flag to indicate whether to create file or parent directories if missing.
        """
        logger.info(
            f"Uploading new data file at {path} for study {uuid}",
            extra={"user": current_user.id},
        )
        path = sanitize_string(path)
        params = RequestParameters(user=current_user)
        study_service.edit_study(uuid, path, file, params, create_missing=create_missing)

    @bp.get(
        "/studies/{uuid}/raw/validate",
        summary="Launch test validation on study",
        tags=[APITag.study_raw_data],
        response_model=t.List[str],
    )
    def validate(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> t.List[str]:
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
