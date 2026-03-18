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
from typing import Annotated, List, Optional

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from starlette.responses import FileResponse

from antarest.core.api_types import SanitizedStr
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.np_array import NpArray
from antarest.core.utils.polars import create_polars_dataframe
from antarest.core.utils.web import APITag
from antarest.dependencies import MatrixServiceDep, TmpExportFileDep, auth_required
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
    bp = APIRouter(prefix="/v1", tags=[APITag.matrix], dependencies=[Depends(auth_required)], route_class=DishkaRoute)

    @bp.post("/matrix", description="Upload a new matrix")
    def create(
        service: MatrixServiceDep,
        matrix: Annotated[List[List[MatrixData]], Body(description="matrix dto")] = [],
    ) -> str:
        logger.info("Creating new matrix")
        return service.create(create_polars_dataframe(matrix))

    @bp.post(
        "/matrix/_import",
        description="Import a new matrix or zip matrices",
    )
    def create_by_importation(
        service: MatrixServiceDep,
        file: Annotated[UploadFile, File()],
        json: bool = False,
    ) -> list[MatrixInfoDTO]:
        logger.info("Importing new matrix dataset")
        return service.create_by_importation(file, is_json=json)

    @bp.get("/matrix", description="Return a list of matrices metadata")
    def get_matrices(service: MatrixServiceDep) -> list[MatrixMetadataDTO]:
        logger.info("Fetching matrices metadatas")
        user = require_current_user()

        if not user.is_site_admin():
            raise UserHasNotPermissionError()

        return service.get_matrices()

    @bp.get("/matrix/{id}")
    def get(service: MatrixServiceDep, id: SanitizedStr) -> MatrixDTO:
        logger.info("Fetching matrix")
        df = service.get(id)
        return MatrixDTO(id=id, index=list(range(len(df))), columns=list(df.columns), data=df.to_numpy())

    @bp.get(
        "/matrix/_references/",
        description="Fetching a list of matrices statistics",
        response_model_exclude_none=True,
    )
    def get_matrices_references(
        service: MatrixServiceDep,
        disk_usage: Annotated[
            bool,
            Query(
                alias="disk_usage", description="Determine if the disk usage should be displayed", title="Disk Usage"
            ),
        ],
    ) -> dict[str, MatrixReferencesDTO]:
        user = require_current_user()
        logger.info("Fetching matrices references")
        if not user.is_site_admin():
            raise UserHasNotPermissionError

        return service.get_matrices_references(disk_usage)

    @bp.post("/matrixdataset")
    def create_dataset(
        service: MatrixServiceDep,
        metadata: Annotated[MatrixDataSetUpdateDTO, Body()],
        matrices: Annotated[List[MatrixInfoDTO], Body()],
    ) -> MatrixDataSetDTO:
        logger.info(f"Creating new matrix dataset metadata {metadata.name}")
        return service.create_dataset(metadata, matrices).to_dto()

    @bp.put(
        "/matrixdataset/{id}/metadata",
    )
    def update_dataset_metadata(
        service: MatrixServiceDep, id: SanitizedStr, metadata: MatrixDataSetUpdateDTO
    ) -> MatrixDataSetDTO:
        logger.info(f"Updating matrix dataset metadata {id}")
        return service.update_dataset(id, metadata).to_dto()

    @bp.get(
        "/matrixdataset/_search",
    )
    def query_datasets(
        service: MatrixServiceDep, name: Optional[SanitizedStr], filter_own: bool = False
    ) -> List[MatrixDataSetDTO]:
        logger.info("Searching matrix dataset metadata")
        return service.list(name, filter_own)

    @bp.get(
        "/matrixdataset/{dataset_id}/download",
        summary="Download dataset",
    )
    def download_dataset(service: MatrixServiceDep, dataset_id: SanitizedStr) -> FileDownloadTaskDTO:
        logger.info(f"Download {dataset_id} matrix dataset")
        return service.download_dataset(dataset_id)

    @bp.get(
        "/matrix/{matrix_id}/download",
        summary="Download matrix content",
    )
    def download_matrix(
        service: MatrixServiceDep,
        tmp_export_file: TmpExportFileDep,
        matrix_id: SanitizedStr,
    ) -> FileResponse:
        logger.info(f"Download {matrix_id} matrix")
        service.download_matrix(matrix_id, tmp_export_file)
        return FileResponse(
            tmp_export_file,
            headers={"Content-Disposition": f'attachment; filename="matrix-{matrix_id}.txt'},
            media_type="text/plain",
        )

    @bp.delete("/matrixdataset/{id}")
    def delete_datasets(service: MatrixServiceDep, id: SanitizedStr) -> None:
        logger.info(f"Removing matrix dataset metadata {id}")
        service.delete_dataset(id)

    @bp.post(
        "/private/resolve-matrix-store",
        summary="Synchronize Database with filesystem for the matrix-store. To be used if an issue occurred",
    )
    def synchronize_matrix_store(service: MatrixServiceDep, dry_run: bool) -> dict[str, MatrixMismatchDTO]:
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
