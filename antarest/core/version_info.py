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

"""
Python module that is dedicated to printing application version and dependencies information
"""

import subprocess
import sys
from importlib.metadata import distributions
from pathlib import Path
from typing import Dict

from antarest.core.serde import AntaresBaseModel


class VersionInfoDTO(AntaresBaseModel):
    name: str = "AntaREST"
    version: str
    gitcommit: str
    dependencies: Dict[str, str] = {}

    class Config:
        json_schema_extra = {
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
        return subprocess.check_output(command, encoding="utf-8").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def get_dependencies() -> Dict[str, str]:
    """
    Retrieve the list of installed dependencies and their versions.
    """
    try:
        return {dist.name: dist.version for dist in distributions() if dist.name.lower() != "antarest"}
    except Exception:
        return _get_dependencies_with_pip()


def _get_dependencies_with_pip() -> Dict[str, str]:
    """
    Fallback using `pip freeze` to retrieve dependencies.
    """
    python_name = Path(sys.executable).with_suffix("").name.lower()
    if not any(python_name.startswith(p) for p in {"python", "jython", "ipy", "pypy"}):
        return {}

    args = [sys.executable, "-m", "pip", "freeze"]
    output = subprocess.check_output(args, encoding="utf-8")
    lines = (line for line in output.splitlines() if "==" in line)
    packages = dict(line.split("==", 1) for line in lines)
    return {k: v for k, v in packages.items() if k.lower() != "antarest"}
