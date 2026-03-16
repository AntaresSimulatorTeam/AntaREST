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

import logging
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from starlette.responses import FileResponse

from antarest.core.api_types import SanitizedStr
from antarest.core.dependencies import auth_required, get_matrix_service, get_tmp_export_file
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.np_array import NpArray
from antarest.core.utils.polars import create_polars_dataframe
from antarest.core.utils.web import APITag
from antarest.login.utils import require_current_user
from antarest.matrixstore.model import (
    MatrixData,
    MatrixDataSetDTO,
    MatrixDataSetUpdateDTO,
    MatrixInfoDTO,
    MatrixMetadataDTO,
    MatrixMismatchDTO,
    MatrixReferencesDTO,
)
from antarest.matrixstore.service import MatrixService

logger = logging.getLogger(__name__)


class MatrixDTO(AntaresBaseModel, arbitrary_types_allowed=True):
    index: list[int]
    columns: list[int | str]
    data: NpArray
    id: str


def create_matrix_api() -> APIRouter:
    """
    Endpoints login implementation
    """
    bp = APIRouter(prefix="/v1", tags=[APITag.matrix], dependencies=[Depends(auth_required)])

    @bp.post("/matrix", description="Upload a new matrix")
    def create(
        matrix: Annotated[List[List[MatrixData]], Body(description="matrix dto")] = [],
        service: MatrixService = Depends(get_matrix_service),
    ) -> str:
        logger.info("Creating new matrix")
        return service.create(create_polars_dataframe(matrix))

    @bp.post(
        "/matrix/_import",
        description="Import a new matrix or zip matrices",
    )
    def create_by_importation(
        file: Annotated[UploadFile, File()],
        json: bool = False,
        service: MatrixService = Depends(get_matrix_service),
    ) -> list[MatrixInfoDTO]:
        logger.info("Importing new matrix dataset")
        return service.create_by_importation(file, is_json=json)

    @bp.get("/matrix", description="Return a list of matrices metadata")
    def get_matrices(service: MatrixService = Depends(get_matrix_service)) -> list[MatrixMetadataDTO]:
        logger.info("Fetching matrices metadatas")
        user = require_current_user()

        if not user.is_site_admin():
            raise UserHasNotPermissionError()

        return service.get_matrices()

    @bp.get("/matrix/{id}")
    def get(id: SanitizedStr, service: MatrixService = Depends(get_matrix_service)) -> MatrixDTO:
        logger.info("Fetching matrix")
        df = service.get(id)
        return MatrixDTO(id=id, index=list(range(len(df))), columns=list(df.columns), data=df.to_numpy())

    @bp.get(
        "/matrix/_references/",
        description="Fetching a list of matrices statistics",
        response_model_exclude_none=True,
    )
    def get_matrices_references(
        disk_usage: Annotated[
            bool,
            Query(
                alias="disk_usage", description="Determine if the disk usage should be displayed", title="Disk Usage"
            ),
        ],
        service: MatrixService = Depends(get_matrix_service),
    ) -> dict[str, MatrixReferencesDTO]:
        user = require_current_user()
        logger.info("Fetching matrices references")
        if not user.is_site_admin():
            raise UserHasNotPermissionError

        return service.get_matrices_references(disk_usage)

    @bp.post("/matrixdataset")
    def create_dataset(
        metadata: Annotated[MatrixDataSetUpdateDTO, Body()],
        matrices: Annotated[List[MatrixInfoDTO], Body()],
        service: MatrixService = Depends(get_matrix_service),
    ) -> MatrixDataSetDTO:
        logger.info(f"Creating new matrix dataset metadata {metadata.name}")
        return service.create_dataset(metadata, matrices).to_dto()

    @bp.put(
        "/matrixdataset/{id}/metadata",
    )
    def update_dataset_metadata(
        id: SanitizedStr, metadata: MatrixDataSetUpdateDTO, service: MatrixService = Depends(get_matrix_service)
    ) -> MatrixDataSetDTO:
        logger.info(f"Updating matrix dataset metadata {id}")
        return service.update_dataset(id, metadata).to_dto()

    @bp.get(
        "/matrixdataset/_search",
    )
    def query_datasets(
        name: Optional[SanitizedStr], filter_own: bool = False, service: MatrixService = Depends(get_matrix_service)
    ) -> List[MatrixDataSetDTO]:
        logger.info("Searching matrix dataset metadata")
        return service.list(name, filter_own)

    @bp.get(
        "/matrixdataset/{dataset_id}/download",
        summary="Download dataset",
    )
    def download_dataset(
        dataset_id: SanitizedStr, service: MatrixService = Depends(get_matrix_service)
    ) -> FileDownloadTaskDTO:
        logger.info(f"Download {dataset_id} matrix dataset")
        return service.download_dataset(dataset_id)

    @bp.get(
        "/matrix/{matrix_id}/download",
        summary="Download matrix content",
    )
    def download_matrix(
        matrix_id: SanitizedStr,
        tmp_export_file: Annotated[Path, Depends(get_tmp_export_file)],
        service: MatrixService = Depends(get_matrix_service),
    ) -> FileResponse:
        logger.info(f"Download {matrix_id} matrix")
        service.download_matrix(matrix_id, tmp_export_file)
        return FileResponse(
            tmp_export_file,
            headers={"Content-Disposition": f'attachment; filename="matrix-{matrix_id}.txt'},
            media_type="text/plain",
        )

    @bp.delete("/matrixdataset/{id}")
    def delete_datasets(id: SanitizedStr, service: MatrixService = Depends(get_matrix_service)) -> None:
        logger.info(f"Removing matrix dataset metadata {id}")
        service.delete_dataset(id)

    @bp.post(
        "/private/resolve-matrix-store",
        summary="Synchronize Database with filesystem for the matrix-store. To be used if an issue occurred",
    )
    def synchronize_matrix_store(
        dry_run: bool, service: MatrixService = Depends(get_matrix_service)
    ) -> dict[str, MatrixMismatchDTO]:
        """
        To be used by the admin only.
        If `dry_run` is True, only returns the list of mismatches. Else, also performs the 2 following operations:
        - Deletes lines from `Matrix` table in DB for matrices that do not exist on the filesystem.
        - Insert lines inside `Matrix` table in DB for matrices that exist on the filesystem but not in the DB.
        """
        user = require_current_user()
        if not user.is_site_admin():
            raise UserHasNotPermissionError()

        return service.synchronize_matrix_store(dry_run=dry_run)

    return bp
