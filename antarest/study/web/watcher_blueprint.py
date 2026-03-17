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
from http import HTTPStatus
from http.client import HTTPException
from typing import List

from fastapi import APIRouter, Depends

from antarest.core.api_types import SanitizedStr
from antarest.core.dependencies import WatcherDep, auth_required
from antarest.core.utils.web import APITag

logger = logging.getLogger(__name__)


class BadPathFormatError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


def create_watcher_routes() -> APIRouter:
    """
    Endpoint implementation for watcher management
    """
    bp = APIRouter(prefix="/v1", tags=[APITag.study_raw_data], dependencies=[Depends(auth_required)])

    @bp.post(
        "/watcher/_scan",
        summary="Launch scan in selected directory",
    )
    def scan_dir(watcher: WatcherDep, path: SanitizedStr, recursive: bool = True) -> str:
        if path:
            # The front actually sends <workspace>/<path/to/folder>
            try:
                path_components: List[str] = path.strip("/").split("/")
                workspace = path_components[0]
                relative_path = "/".join(path_components[1:])
            except Exception as e:
                logger.error(
                    "Unexpected exception when tying to retrieve scan path components",
                    exc_info=e,
                )
                raise BadPathFormatError("Bad path format. Expected <workspace>/<path/to/folder>")
            logger.info(f"Scanning directory {relative_path} of worskpace {workspace}")
        else:
            logger.info("Scanning all workspaces")
            relative_path = None
            workspace = None
        return watcher.oneshot_scan(recursive=recursive, workspace=workspace, path=relative_path)

    return bp
