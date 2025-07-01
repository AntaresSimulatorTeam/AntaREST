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

import logging
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd
from fastapi import APIRouter, Body, Depends, File, UploadFile
from starlette.responses import FileResponse

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.login.utils import require_current_user
from antarest.matrixstore.model import (
    MatrixData,
    MatrixDataSetDTO,
    MatrixDataSetUpdateDTO,
    MatrixInfoDTO,
    MatrixMetadataDTO,
)
from antarest.matrixstore.service import MatrixService

logger = logging.getLogger(__name__)


class MatrixDTO(AntaresBaseModel, arbitrary_types_allowed=True):
    index: list[int | str]
    columns: list[int | str]
    data: list[list[float | int | str]]
    id: str = ""


def create_matrix_api(service: MatrixService, ftm: FileTransferManager, config: Config) -> APIRouter:
    """
    Endpoints login implementation
    Args:
        service: login facade service
        ftm: file transfer manager
        config: server config

    Returns:

    """
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", dependencies=[auth.required()])

    @bp.post("/matrix", tags=[APITag.matrix], description="Upload a new matrix")
    def create(matrix: List[List[MatrixData]] = Body(description="matrix dto", default=[])) -> str:
        logger.info("Creating new matrix")
        return service.create(pd.DataFrame(matrix))

    @bp.post(
        "/matrix/_import",
        tags=[APITag.matrix],
        description="Import a new matrix or zip matrices",
        response_model=List[MatrixInfoDTO],
    )
    def create_by_importation(
        json: bool = False,
        file: UploadFile = File(...),
    ) -> Any:
        logger.info("Importing new matrix dataset")
        return service.create_by_importation(file, is_json=json)

    @bp.get("/matrix", tags=[APITag.matrix], description="Return a list of matrices metadata")
    def get_matrices() -> list[MatrixMetadataDTO]:
        logger.info("Fetching matrices metadatas")
        user = require_current_user()

        if not user.is_site_admin():
            raise UserHasNotPermissionError()

        return service.get_matrices()

    @bp.get("/matrix/{id}", tags=[APITag.matrix])
    def get(id: str) -> MatrixDTO:
        logger.info("Fetching matrix")
        df = service.get(id)
        return MatrixDTO.model_construct(
            id=id,
            index=list(df.index),
            columns=list(df.columns),
            data=df.to_numpy().tolist(),
        )

    @bp.post("/matrixdataset", tags=[APITag.matrix], response_model=MatrixDataSetDTO)
    def create_dataset(metadata: MatrixDataSetUpdateDTO = Body(...), matrices: List[MatrixInfoDTO] = Body(...)) -> Any:
        logger.info(f"Creating new matrix dataset metadata {metadata.name}")
        return service.create_dataset(metadata, matrices).to_dto()

    @bp.put(
        "/matrixdataset/{id}/metadata",
        tags=[APITag.matrix],
        response_model=MatrixDataSetDTO,
    )
    def update_dataset_metadata(id: str, metadata: MatrixDataSetUpdateDTO) -> Any:
        logger.info(f"Updating matrix dataset metadata {id}")
        return service.update_dataset(id, metadata).to_dto()

    @bp.get(
        "/matrixdataset/_search",
        tags=[APITag.matrix],
        response_model=List[MatrixDataSetDTO],
    )
    def query_datasets(name: Optional[str], filter_own: bool = False) -> Any:
        logger.info("Searching matrix dataset metadata")
        return service.list(name, filter_own)

    @bp.get(
        "/matrixdataset/{dataset_id}/download",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
    )
    def download_dataset(dataset_id: str) -> Any:
        logger.info(f"Download {dataset_id} matrix dataset")
        return service.download_dataset(dataset_id)

    @bp.get(
        "/matrix/{matrix_id}/download",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
    )
    def download_matrix(
        matrix_id: str,
        tmp_export_file: Path = Depends(ftm.request_tmp_file),
    ) -> Any:
        logger.info(f"Download {matrix_id} matrix")
        service.download_matrix(matrix_id, tmp_export_file)
        return FileResponse(
            tmp_export_file,
            headers={"Content-Disposition": f'attachment; filename="matrix-{matrix_id}.txt'},
            media_type="text/plain",
        )

    @bp.delete("/matrixdataset/{id}", tags=[APITag.matrix])
    def delete_datasets(id: str) -> Any:
        logger.info(f"Removing matrix dataset metadata {id}")
        service.delete_dataset(id)

    return bp
