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

from fastapi import APIRouter, Body, Depends, File, UploadFile
from starlette.responses import FileResponse

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.matrixstore.model import MatrixData, MatrixDataSetDTO, MatrixDataSetUpdateDTO, MatrixDTO, MatrixInfoDTO
from antarest.matrixstore.service import MatrixService

logger = logging.getLogger(__name__)


def create_matrix_api(service: MatrixService, ftm: FileTransferManager, config: Config) -> APIRouter:
    """
    Endpoints login implementation
    Args:
        service: login facade service
        ftm: file transfer manager
        config: server config

    Returns:

    """
    bp = APIRouter(prefix="/v1")

    auth = Auth(config)

    @bp.post("/matrix", tags=[APITag.matrix], description="Upload a new matrix")
    def create(
        matrix: List[List[MatrixData]] = Body(description="matrix dto", default=[]),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info("Creating new matrix")
        if current_user.id is not None:
            return service.create(matrix)
        raise UserHasNotPermissionError()

    @bp.post(
        "/matrix/_import",
        tags=[APITag.matrix],
        description="Import a new matrix or zip matrices",
        response_model=List[MatrixInfoDTO],
    )
    def create_by_importation(
        json: bool = False,
        file: UploadFile = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info("Importing new matrix dataset")
        if current_user.id is not None:
            return service.create_by_importation(file, is_json=json)
        raise UserHasNotPermissionError()

    @bp.get("/matrix/{id}", tags=[APITag.matrix], response_model=MatrixDTO)
    def get(id: str, user: JWTUser = Depends(auth.get_current_user)) -> MatrixDTO:
        logger.info("Fetching matrix")
        if user.id is not None:
            return service.get(id)
        raise UserHasNotPermissionError()

    @bp.post("/matrixdataset", tags=[APITag.matrix], response_model=MatrixDataSetDTO)
    def create_dataset(
        metadata: MatrixDataSetUpdateDTO = Body(...),
        matrices: List[MatrixInfoDTO] = Body(...),
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Creating new matrix dataset metadata {metadata.name}")
        request_params = RequestParameters(user=user)
        return service.create_dataset(metadata, matrices, request_params).to_dto()

    @bp.put(
        "/matrixdataset/{id}/metadata",
        tags=[APITag.matrix],
        response_model=MatrixDataSetDTO,
    )
    def update_dataset_metadata(
        id: str,
        metadata: MatrixDataSetUpdateDTO,
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Updating matrix dataset metadata {id}")
        request_params = RequestParameters(user=user)
        return service.update_dataset(id, metadata, request_params).to_dto()

    @bp.get(
        "/matrixdataset/_search",
        tags=[APITag.matrix],
        response_model=List[MatrixDataSetDTO],
    )
    def query_datasets(
        name: Optional[str],
        filter_own: bool = False,
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info("Searching matrix dataset metadata")
        request_params = RequestParameters(user=user)
        return service.list(name, filter_own, request_params)

    @bp.get(
        "/matrixdataset/{dataset_id}/download",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
    )
    def download_dataset(
        dataset_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Download {dataset_id} matrix dataset")
        params = RequestParameters(user=current_user)
        return service.download_dataset(dataset_id, params)

    @bp.get(
        "/matrix/{matrix_id}/download",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
    )
    def download_matrix(
        matrix_id: str,
        tmp_export_file: Path = Depends(ftm.request_tmp_file),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Download {matrix_id} matrix")
        params = RequestParameters(user=current_user)
        service.download_matrix(matrix_id, tmp_export_file, params)
        return FileResponse(
            tmp_export_file,
            headers={"Content-Disposition": f'attachment; filename="matrix-{matrix_id}.txt'},
            media_type="text/plain",
        )

    @bp.delete("/matrixdataset/{id}", tags=[APITag.matrix])
    def delete_datasets(
        id: str,
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Removing matrix dataset metadata {id}")
        request_params = RequestParameters(user=user)
        service.delete_dataset(id, request_params)

    return bp
