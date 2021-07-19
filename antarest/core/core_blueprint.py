import subprocess
from pathlib import Path
from typing import Any, Optional
from fastapi import APIRouter

from antarest import __version__
from antarest.core.config import Config
from antarest.core.utils.web import APITag


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


def create_utils_routes(config: Config) -> APIRouter:
    """
    Utility endpoints

    Args:
        storage_service: storage service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter()

    @bp.get("/health", tags=[APITag.misc])
    def health() -> Any:
        return {"status": "available"}

    @bp.get("/version", tags=[APITag.misc], summary="Get application version")
    def version() -> Any:
        version_data = {"version": __version__}

        commit_id = get_commit_id(config.resources_path)
        if commit_id is not None:
            version_data["gitcommit"] = commit_id

        return version_data

    return bp
