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
from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from starlette.websockets import WebSocket, WebSocketDisconnect

from antarest.core.api_types import SanitizedStr
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.dependencies import AuthDep, ConfigDep, ConnectionManagerDep
from antarest.login.auth import get_user_from_token

logger = logging.getLogger(__name__)


def register_websocket_routes(api_root: APIRouter) -> None:
    """Register the /ws websocket route"""

    @api_root.websocket("/ws")
    async def connect(
        websocket: WebSocket,
        token: Annotated[SanitizedStr, Query()],
        jwt_manager: AuthDep,
        config: ConfigDep,
        ws_manager: ConnectionManagerDep,
    ) -> None:
        user: JWTUser | None = None
        if not config.security.disabled:
            try:
                if not token:
                    raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

                # TODO: does not verify against revoked tokens ?
                user = get_user_from_token(token, jwt_manager)
                if user is None:
                    raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)
            except Exception as e:
                logger.error(
                    "Failed to check token from websocket connexion",
                    exc_info=e,
                )
                raise HTTPException(500, "Failed to check auth")
        await ws_manager.connect(websocket, user or DEFAULT_ADMIN_USER)
        try:
            while True:
                message = await websocket.receive_text()
                try:
                    ws_manager.process_message(message, websocket)
                except Exception as e:
                    logger.error(
                        f"Failed to process websocket message {message}",
                        exc_info=e,
                    )
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
