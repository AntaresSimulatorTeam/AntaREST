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

from typing import Any

from fastapi import APIRouter

from antarest.core.config import Config
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.web import APITag
from antarest.core.version_info import VersionInfoDTO, get_commit_id, get_dependencies


class StatusDTO(AntaresBaseModel):
    status: str


class DesktopModeDTO(AntaresBaseModel):
    desktop_mode: bool


def create_utils_routes(config: Config) -> APIRouter:
    """
    Utility endpoints

    Args:
        config: main server configuration
    """
    bp = APIRouter()

    @bp.get("/health", tags=[APITag.misc], response_model=StatusDTO)
    def health() -> Any:
        return StatusDTO(status="available")

    @bp.get(
        "/version",
        tags=[APITag.misc],
        summary="Get application version",
    )
    def version_info(with_deps: bool = False) -> VersionInfoDTO:
        """
        Returns the current version of the application, along with relevant dependency information.

        - `name`: The name of the application.
        - `version`: The current version of the application.
        - `gitcommit`: The commit ID of the current version's Git repository.
        - `dependencies`: A dictionary of dependencies, where the key is
          the dependency name and the value is its version number.
        """
        from antarest import __version__ as antarest_version

        return VersionInfoDTO(
            version=antarest_version,
            gitcommit=get_commit_id(config.resources_path),
            dependencies=get_dependencies() if with_deps else {},
        )

    @bp.get(
        "/desktop_mode",
        tags=[APITag.misc],
        summary="Get if application is running on desktop mode",
        response_model=DesktopModeDTO,
    )
    def desktop_mode() -> Any:
        """
        Returns weither the application is running on desktop mode.

        - `desktop_mode`: boolean.
        """

        return DesktopModeDTO(desktop_mode=config.desktop_mode)

    return bp
