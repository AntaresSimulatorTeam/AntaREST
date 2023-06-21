"""
Python module that is dedicated to printing application version and dependencies information
"""
import os
import subprocess
from pathlib import Path
from typing import Dict
import sys

from pydantic import BaseModel


RUN_ON_WINDOWS = os.name == "nt"


class VersionInfoDTO(BaseModel):
    name: str = "AntaREST"
    version: str
    gitcommit: str
    dependencies: Dict[str, str]

    class Config:
        schema_extra = {
            "example": {
                "name": "AntaREST",
                "version": "2.13.2",
                "gitcommit": "879d9d641fc2e7e30e626084b431ce014de63532",
                "dependencies": {
                    "click": "8.0.4",
                    "Deprecated": "1.2.13",
                    "fastapi": "0.73.0",
                    "Flask": "2.1.3",
                    "gunicorn": "20.1.0",
                },
            }
        }


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
    command = ["git", "log", "-1", "HEAD", "--format=%H"]
    try:
        return subprocess.check_output(
            command, encoding="utf-8", shell=RUN_ON_WINDOWS
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def get_dependencies() -> Dict[str, str]:
    """
    Retrieve the list of installed dependencies and their versions.

    Returns:
        A dictionary containing the package names and their corresponding versions installed in the
        current Python environment. The dictionary keys are the package names (as strings), and the
        values are the corresponding version numbers (also as strings).

    Raises:
        subprocess.CalledProcessError:
            If the `pip freeze` command fails for some reason.
    """
    # fmt: off
    pip_path = str(Path(sys.executable).parent / "pip.exe") if RUN_ON_WINDOWS else "pip"
    output = subprocess.check_output([pip_path, "freeze"], encoding="utf-8", shell=RUN_ON_WINDOWS)
    lines = (
        line
        for line in output.splitlines(keepends=False)
        if "==" in line
    )
    # noinspection PyTypeChecker
    packages = dict(line.split("==", 1) for line in lines)
    # AntaREST is not a dependency of AntaREST
    return {k: v for k, v in packages.items() if k.lower() != "antarest"}
    # fmt: on
