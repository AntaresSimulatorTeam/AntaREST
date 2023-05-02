"""
Python module that is dedicated to printing application version and dependencies information
"""
import subprocess
from pathlib import Path
from typing import Dict

from pydantic import BaseModel


class VersionInfoDTO(BaseModel):
    name: str = "AntaREST"
    version: str
    gitcommit: str
    dependencies: Dict[str, str]


def get_commit_id(resources_dir: Path) -> str:
    """
    Returns the contents of the file :file:`resources/commit_id`
    if it exists and is not empty, or the commit ID of the current Git HEAD, if available.
    If neither the commit ID nor the file is available, returns "".

    Note:
        The :file:`commit_id` is generated during the "deploy" stage
        in the :file:`.github/workflows/deploy.yml` GitHub workflow.

    Args:
        resources_dir: The path to the ``resources`` directory.

    Returns:
        The contents of the file :file:`resources/commit_id`,
        the commit ID of the current Git HEAD, or "".
    """
    path_commit_id = resources_dir.joinpath("commit_id")
    try:
        return path_commit_id.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return get_last_commit_from_git()


def get_last_commit_from_git() -> str:
    """Returns the commit ID of the current Git HEAD, or ""."""
    command = "git log -1 HEAD --format=%H"
    try:
        return subprocess.check_output(
            command, encoding="utf-8", shell=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def get_dependencies() -> Dict[str, str]:
    """
    Returns the list of installed dependencies and their versions.
    """
    return dict(
        line.split("==", 1)
        for line in subprocess.check_output("pip freeze", shell=True)
        .decode("utf-8")
        .splitlines(keepends=False)
        if "==" in line and "antarest" not in line.lower()
    )
