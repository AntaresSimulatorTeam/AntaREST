from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends, Body, Query

from antarest.common.config import Config
from antarest.common.jwt import JWTUser
from antarest.common.requests import (
    UserHasNotPermissionError,
    RequestParameters,
)
from antarest.common.utils.web import APITag
from antarest.login.auth import Auth
from antarest.matrixstore.model import (
    MatrixDTO,
    MatrixFreq,
    MatrixUserMetadataQuery,
    MatrixUserMetadata,
)
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

    @bp.put("/matrix/{id}/metadata", tags=[APITag.matrix])
    def update_metadata(
        id: str,
        name: Optional[str] = Query(None),
        groups: Optional[List[str]] = Query(None),
        public: Optional[bool] = Query(None),
        metadata: Optional[Dict[str, str]] = Body(default=None, embed=False),
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=user)
        result: Optional[MatrixUserMetadata] = None
        if metadata is not None:
            result = service.update_metadata(
                id, user.id, metadata, request_params
            )
        if name is not None:
            result = service.set_name(id, user.id, name, request_params)
        if groups is not None:
            result = service.update_group(id, user.id, groups, request_params)
        if public is not None:
            result = service.set_public(id, user.id, public, request_params)
        return result.to_dto() if result else None

    @bp.post("/matrix/_search", tags=[APITag.matrix])
    def query_metadata(
        query: MatrixUserMetadataQuery,
        user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=user)
        return service.list(query, request_params)

    return bp
