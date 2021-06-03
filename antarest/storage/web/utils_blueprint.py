import subprocess
from http import HTTPStatus
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, File, Depends
from starlette.responses import StreamingResponse

from antarest.common.jwt import JWTUser
from antarest.login.auth import Auth
from antarest.common.config import Config
from antarest.common.requests import (
    RequestParameters,
)
from antarest.storage.service import StorageService
from antarest import __version__


def get_commit_id(path_resources: Path) -> Optional[str]:

    commit_id = None

    path_commit_id = path_resources / "commit_id"
    if path_commit_id.exists():
        commit_id = path_commit_id.read_text()[:-1]
    else:
        command = "git log -1 HEAD --format=%H"
        process = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
        if process.returncode == 0:
            commit_id = process.stdout.decode("utf-8")

    if commit_id is not None:

        def remove_carriage_return(value: str) -> str:
            return value[:-1]

        commit_id = remove_carriage_return(commit_id)

    return commit_id


def create_utils_routes(
    storage_service: StorageService, config: Config
) -> APIRouter:
    """
    Utility endpoints

    Args:
        storage_service: storage service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter()

    auth = Auth(config)

    @bp.get("/file/{path:path}", tags=["Manage Matrix"], summary="Get file")
    def get_file(
        path: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        try:
            params = RequestParameters(user=current_user)
            return StreamingResponse(storage_service.get_matrix(path, params))
        except FileNotFoundError:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND.value,
                detail=f"{path} not found",
            )

    @bp.post(
        "/file/{path:path}",
        status_code=HTTPStatus.NO_CONTENT.value,
        tags=["Manage Matrix"],
        summary="Post file",
    )
    def post_file(
        path: str,
        matrix: bytes = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        storage_service.upload_matrix(path, matrix, params)

        return ""

    @bp.get("/health", tags=["Misc"])
    def health() -> Any:
        return {"status": "available"}

    @bp.get("/version", tags=["Misc"], summary="Get application version")
    def version() -> Any:
        version_data = {"version": __version__}

        commit_id = get_commit_id(storage_service.study_service.path_resources)
        if commit_id is not None:
            version_data["gitcommit"] = commit_id

        return version_data

    return bp
