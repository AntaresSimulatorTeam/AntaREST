# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
This module contains the logic necessary to serve both
the front-end application and the backend HTTP application.

This includes:
 - serving static frontend files
 - redirecting "not found" requests to home, which itself redirects to index.html
 - providing the endpoint /config.json, which the front-end uses to know
   what are the API and websocket prefixes
"""

import re
from pathlib import Path
from typing import Any, Optional, Sequence

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp

from antarest.core.utils.string import to_camel_case


class RedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware that rewrites the URL path to "/" for incoming requests
    that do not match the known end points. This is useful for redirecting requests
    to the main page of a ReactJS application when the user refreshes the browser.
    """

    def __init__(
        self,
        app: ASGIApp,
        dispatch: Optional[DispatchFunction] = None,
        route_paths: Sequence[str] = (),
    ) -> None:
        """
        Initializes an instance of the URLRewriterMiddleware.

        Args:
            app: The ASGI application to which the middleware is applied.
            dispatch: The dispatch function to use.
            route_paths: The known route paths of the application.
                Requests that do not match any of these paths will be rewritten to the root path.

        Note:
            The `route_paths` should contain all the known endpoints of the application.
        """
        dispatch = self.dispatch if dispatch is None else dispatch
        super().__init__(app, dispatch)
        self.known_prefixes = {re.findall(r"/(?:(?!/).)*", p)[0] for p in route_paths if p != "/"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Any:
        """
        Intercepts the incoming request and rewrites the URL path if necessary.
        Passes the modified or original request to the next middleware or endpoint handler.
        """
        url_path = request.scope["path"]
        if url_path in {"", "/"}:
            pass
        elif not any(url_path.startswith(ep) for ep in self.known_prefixes):
            request.scope["path"] = "/"
        return await call_next(request)


class BackEndConfig(BaseModel):
    """
    Configuration about backend URLs served to the frontend.
    """

    rest_endpoint: str
    ws_endpoint: str

    class Config:
        populate_by_name = True
        alias_generator = to_camel_case


def create_backend_config(api_prefix: str) -> BackEndConfig:
    if not api_prefix.startswith("/"):
        api_prefix = "/" + api_prefix
    return BackEndConfig(rest_endpoint=f"{api_prefix}", ws_endpoint=f"{api_prefix}/ws")


def add_front_app(application: FastAPI, resources_dir: Path, api_prefix: str) -> None:
    """
    This functions adds the logic necessary to serve both
    the front-end application and the backend HTTP application.

    This includes:
     - serving static frontend files
     - redirecting "not found" requests to home, which itself redirects to index.html
     - providing the endpoint /config.json, which the front-end uses to know
       what are the API and websocket prefixes
    """
    backend_config = create_backend_config(api_prefix)

    front_app_dir = resources_dir / "webapp"

    # Serve front-end files
    application.mount(
        "/static",
        StaticFiles(directory=front_app_dir),
        name="static",
    )

    # Redirect home to index.html
    @application.get("/", include_in_schema=False)
    def home(request: Request) -> Any:
        return FileResponse(front_app_dir / "index.html", 200)

    # Serve config for the front-end at /config.json
    @application.get("/config.json", include_in_schema=False)
    def get_api_paths_config(request: Request) -> BackEndConfig:
        return backend_config

    # When the web application is running in Desktop mode, the ReactJS web app
    # is served at the `/static` entry point. Any requests that are not API
    # requests should be redirected to the `index.html` file, which will handle
    # the route provided by the URL.
    route_paths = [r.path for r in application.routes]  # type: ignore
    application.add_middleware(
        RedirectMiddleware,
        route_paths=route_paths,
    )
