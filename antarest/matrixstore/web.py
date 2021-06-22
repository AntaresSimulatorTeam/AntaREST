from typing import Any

from fastapi import APIRouter, Depends, Body, Query

from antarest.common.config import Config
from antarest.common.jwt import JWTUser
from antarest.common.requests import UserHasNotPermissionError
from antarest.common.utils.web import APITag
from antarest.login.auth import Auth
from antarest.matrixstore.model import MatrixDTO, MatrixFreq
from antarest.matrixstore.service import MatrixService


def create_matrix_api(service: MatrixService, config: Config) -> APIRouter:
    """
    Endpoints login implementation
    Args:
        service: login facade service
        config: server config
        jwt: jwt manager

    Returns:

    """
    bp = APIRouter(prefix="/v1")

    auth = Auth(config)

    @bp.post("/matrix", tags=[APITag.matrix])
    def create(
        matrix: MatrixDTO = Body(description="matrix dto", default={}),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        if current_user.id is not None:
            return service.create(matrix)
        raise UserHasNotPermissionError()

    @bp.get("/matrix/{id}", tags=[APITag.matrix])
    def get(id: str, user: JWTUser = Depends(auth.get_current_user)) -> Any:
        if user.id is not None:
            return service.get(id)
        raise UserHasNotPermissionError()

    @bp.get("/matrix", tags=[APITag.matrix])
    def get_by_type_or_freq(
        freq: int = Query(None),
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        if user.id is not None:
            return service.get_by_freq(
                freq=MatrixFreq(freq) if freq else None,
            )

    return bp
