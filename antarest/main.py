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

import argparse
import copy
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple, cast

import pydantic
import uvicorn
import uvicorn.config
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from ratelimit import RateLimitMiddleware  # type: ignore
from ratelimit.backends.redis import RedisBackend  # type: ignore
from ratelimit.backends.simple import MemoryBackend  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.types import ASGIApp

from antarest import __version__
from antarest.core.config import Config
from antarest.core.core_blueprint import create_utils_routes
from antarest.core.filesystem_blueprint import create_file_system_blueprint
from antarest.core.logging.utils import LoggingMiddleware, configure_logger
from antarest.core.requests import RATE_LIMIT_CONFIG
from antarest.core.swagger import customize_openapi
from antarest.core.tasks.model import cancel_orphan_tasks
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.core.utils.utils import get_local_path
from antarest.core.utils.web import tags_metadata
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.auth import Auth, JwtSettings
from antarest.login.model import init_admin_user
from antarest.matrixstore.matrix_garbage_collector import MatrixGarbageCollector
from antarest.singleton_services import start_all_services
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.tools.admin_lib import clean_locks
from antarest.utils import SESSION_ARGS, Module, create_services, init_db_engine

logger = logging.getLogger(__name__)


class PathType:
    """file or directory path type for `argparse` parser

    The `PathType` class represents a type of argument that can be used
    with the `argparse` library.
    This class takes three boolean arguments, `exists`, `file_ok`, and `dir_ok`,
    which specify whether the path argument must exist, whether it can be a file,
    and whether it can be a directory, respectively.

    Example Usage::

        import argparse
        from antarest.main import PathType

        parser = argparse.ArgumentParser()
        parser.add_argument("--input", type=PathType(file_ok=True, exists=True))
        args = parser.parse_args()

        print(args.input)

    In the above example, `PathType` is used to specify the type of the `--input`
    argument for the `argparse` parser. The argument must be an existing file path.
    If the given path is not an existing file, the argparse library raises an error.
    The Path object representing the given path is then printed to the console.
    """

    def __init__(
        self,
        exists: bool = False,
        file_ok: bool = False,
        dir_ok: bool = False,
    ) -> None:
        if not (file_ok or dir_ok):
            msg = "Either `file_ok` or `dir_ok` must be set at a minimum."
            raise ValueError(msg)
        self.exists = exists
        self.file_ok = file_ok
        self.dir_ok = dir_ok

    def __call__(self, string: str) -> Path:
        """
        Check whether the given string represents a valid path.

        If `exists` is `False`, the method simply returns the given path.
        If `exists` is True, it checks whether the path exists and whether it is
        a file or a directory, depending on the values of `file_ok` and `dir_ok`.
        If the path exists and is of the correct type, the method returns the path;
        otherwise, it raises an :class:`argparse.ArgumentTypeError` with an
        appropriate error message.

        Args:
            string: file or directory path

        Returns:
            the file or directory path

        Raises
            argparse.ArgumentTypeError: if the path is invalid
        """
        file_path = Path(string).expanduser()
        if not self.exists:
            return file_path
        if self.file_ok and self.dir_ok:
            if file_path.exists():
                return file_path
            msg = f"The file or directory path does not exist: '{file_path}'"
            raise argparse.ArgumentTypeError(msg)
        elif self.file_ok:
            if file_path.is_file():
                return file_path
            elif file_path.exists():
                msg = f"The path is not a regular file: '{file_path}'"
            else:
                msg = f"The file path does not exist: '{file_path}'"
            raise argparse.ArgumentTypeError(msg)
        elif self.dir_ok:
            if file_path.is_dir():
                return file_path
            elif file_path.exists():
                msg = f"The path is not a directory: '{file_path}'"
            else:
                msg = f"The directory path does not exist: '{file_path}'"
            raise argparse.ArgumentTypeError(msg)
        else:  # pragma: no cover
            raise NotImplementedError((self.file_ok, self.dir_ok))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        type=PathType(exists=True, file_ok=True),
        dest="config_file",
        help="path to the config file [default: '%(default)s']",
        default="./config.yaml",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Display the server version and exit",
        version=__version__,
    )
    parser.add_argument(
        "--no-front",
        dest="no_front",
        help="Exclude the embedding of the front-end build",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--auto-upgrade-db",
        dest="auto_upgrade_db",
        help="Automatically upgrade db",
        action="store_true",
        default=False,
    )
    # noinspection PyUnresolvedReferences
    parser.add_argument(
        "--module",
        type=Module,
        dest="module",
        help="Select a module to run [default: application server]",
        choices=[mod.value for mod in Module],
        action="store",
        default=Module.APP.value,
    )
    return parser.parse_args()


class URLRewriterMiddleware(BaseHTTPMiddleware):
    """
    Middleware that rewrites the URL path to "/" (root path) for incoming requests
    that do not match the known end points. This is useful for redirecting requests
    to the main page of a ReactJS application when the user refreshes the browser.
    """

    def __init__(
        self,
        app: ASGIApp,
        dispatch: Optional[DispatchFunction] = None,
        root_path: str = "",
        route_paths: Sequence[str] = (),
    ) -> None:
        """
        Initializes an instance of the URLRewriterMiddleware.

        Args:
            app: The ASGI application to which the middleware is applied.
            dispatch: The dispatch function to use.
            root_path: The root path of the application.
                The URL path will be rewritten relative to this root path.
            route_paths: The known route paths of the application.
                Requests that do not match any of these paths will be rewritten to the root path.

        Note:
            The `root_path` can be set to a specific component of the URL path, such as "api".
            The `route_paths` should contain all the known endpoints of the application.
        """
        dispatch = self.dispatch if dispatch is None else dispatch
        super().__init__(app, dispatch)
        self.root_path = f"/{root_path}" if root_path else ""
        self.known_prefixes = {re.findall(r"/(?:(?!/).)*", p)[0] for p in route_paths if p != "/"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Any:
        """
        Intercepts the incoming request and rewrites the URL path if necessary.
        Passes the modified or original request to the next middleware or endpoint handler.
        """
        url_path = request.scope["path"]
        if url_path in {"", "/"}:
            pass
        elif self.root_path and url_path.startswith(self.root_path):
            request.scope["path"] = url_path[len(self.root_path) :]
        elif not any(url_path.startswith(ep) for ep in self.known_prefixes):
            request.scope["path"] = "/"
        return await call_next(request)


def fastapi_app(
    config_file: Path,
    resource_path: Optional[Path] = None,
    mount_front: bool = True,
    auto_upgrade_db: bool = False,
) -> Tuple[FastAPI, Dict[str, Any]]:
    res = resource_path or get_local_path() / "resources"
    config = Config.from_yaml_file(res=res, file=config_file)
    configure_logger(config)

    logger.info("Initiating application")

    application = FastAPI(
        title="AntaREST",
        version=__version__,
        docs_url=None,
        root_path=config.root_path,
        openapi_tags=tags_metadata,
    )

    # Database
    engine = init_db_engine(config_file, config, auto_upgrade_db)
    application.add_middleware(DBSessionMiddleware, custom_engine=engine, session_args=SESSION_ARGS)
    # Since Starlette Version 0.24.0, the middlewares are lazily build inside this function
    # But we need to instantiate this middleware as it's needed for the study service.
    # So we manually instantiate it here.
    DBSessionMiddleware(None, custom_engine=engine, session_args=cast(Dict[str, bool], SESSION_ARGS))

    application.add_middleware(LoggingMiddleware)

    if mount_front:
        application.mount(
            "/static",
            StaticFiles(directory=str(res / "webapp")),
            name="static",
        )
        templates = Jinja2Templates(directory=str(res / "templates"))

        @application.get("/", include_in_schema=False)
        def home(request: Request) -> Any:
            return templates.TemplateResponse("index.html", {"request": request})

    else:
        # noinspection PyUnusedLocal
        @application.get("/", include_in_schema=False)
        def home(request: Request) -> Any:
            return ""

    @application.on_event("startup")
    def set_default_executor() -> None:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        loop = asyncio.get_running_loop()
        loop.set_default_executor(ThreadPoolExecutor(max_workers=config.server.worker_threadpool_size))

    # TODO move that elsewhere
    @AuthJWT.load_config  # type: ignore
    def get_config() -> JwtSettings:
        return JwtSettings(
            authjwt_secret_key=config.security.jwt_key,
            authjwt_token_location=("headers", "cookies"),
            authjwt_access_token_expires=Auth.ACCESS_TOKEN_DURATION,
            authjwt_refresh_token_expires=Auth.REFRESH_TOKEN_DURATION,
            authjwt_cookie_csrf_protect=False,
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(create_utils_routes(config))
    application.include_router(create_file_system_blueprint(config))

    # noinspection PyUnusedLocal
    @application.exception_handler(HTTPException)
    def handle_http_exception(request: Request, exc: HTTPException) -> Any:
        """
        Custom exception handler to return JSON response for HTTP errors.

        Args:
            request: The incoming request object.
            exc: The raised exception.

        Returns:
            The JSON response containing error details.
        """
        logger.error("HTTP Exception", exc_info=exc)
        return JSONResponse(
            content={
                "description": exc.detail,
                "exception": exc.__class__.__name__,
            },
            status_code=exc.status_code,
        )

    # noinspection PyUnusedLocal
    @application.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError) -> Any:
        """
        Custom exception handler to return JSON response for `RequestValidationError`.

        Args:
            request: The incoming request object.
            exc: The raised exception.

        Returns:
            The JSON response containing error details.
        """
        error_message = exc.errors()[0]["msg"]
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(
                {
                    "description": error_message,
                    "exception": "RequestValidationError",
                    "body": exc.body,
                }
            ),
        )

    # noinspection PyUnusedLocal
    @application.exception_handler(pydantic.ValidationError)
    def handle_validation_error(request: Request, exc: pydantic.ValidationError) -> Any:
        """
        Custom exception handler to return JSON response for `ValidationError`.

        This exception is usually raised during Study configuration reading
        (not when using an end point).

        Args:
            request: The incoming request object.
            exc: The raised exception.

        Returns:
            The JSON response containing error details.
        """
        return JSONResponse(
            content={
                "description": f"{exc}",
                "exception": exc.__class__.__name__,
                "body": exc.json(),
            },
            status_code=422,
        )

    # noinspection PyUnusedLocal
    @application.exception_handler(Exception)
    def handle_all_exception(request: Request, exc: Exception) -> Any:
        """
        Custom exception handler to return JSON response for HTTP errors.

        Args:
            request: The incoming request object.
            exc: The raised exception.

        Returns:
            The JSON response containing error details.
        """
        logger.error("Unexpected Exception", exc_info=exc)
        return JSONResponse(
            content={
                "description": f"Unexpected server error: {exc}",
                "exception": exc.__class__.__name__,
            },
            status_code=500,
        )

    # rate limiter
    auth_manager = Auth(config)
    application.add_middleware(
        RateLimitMiddleware,
        authenticate=auth_manager.create_auth_function(),
        backend=(
            MemoryBackend()
            if config.redis is None
            else RedisBackend(config.redis.host, config.redis.port, 1, config.redis.password)
        ),
        config=RATE_LIMIT_CONFIG,
    )

    init_admin_user(engine=engine, session_args=SESSION_ARGS, admin_password=config.security.admin_pwd)
    services = create_services(config, application)

    if mount_front:
        # When the web application is running in Desktop mode, the ReactJS web app
        # is served at the `/static` entry point. Any requests that are not API
        # requests should be redirected to the `index.html` file, which will handle
        # the route provided by the URL.
        route_paths = [r.path for r in application.routes]  # type: ignore
        application.add_middleware(
            URLRewriterMiddleware,
            root_path=application.root_path,
            route_paths=route_paths,
        )

    if config.server.services and Module.WATCHER.value in config.server.services:
        watcher = cast(Watcher, services["watcher"])
        watcher.start()

    if config.server.services and Module.MATRIX_GC.value in config.server.services:
        matrix_gc = cast(MatrixGarbageCollector, services["matrix_gc"])
        matrix_gc.start()

    if config.server.services and Module.AUTO_ARCHIVER.value in config.server.services:
        auto_archiver = cast(AutoArchiveService, services["auto_archiver"])
        auto_archiver.start()

    customize_openapi(application)
    cancel_orphan_tasks(engine=engine, session_args=SESSION_ARGS)
    return application, services


LOGGING_CONFIG = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
# noinspection SpellCheckingInspection
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "[%(asctime)s] [%(process)s] %(levelprefix)s  %(message)s"
# noinspection SpellCheckingInspection
LOGGING_CONFIG["formatters"]["access"]["fmt"] = (
    "[%(asctime)s] [%(process)s] [%(name)s]"
    " %(levelprefix)s"
    ' %(client_addr)s - "%(request_line)s"'
    " %(status_code)s"
)


def main() -> None:
    arguments = parse_arguments()
    if arguments.module == Module.APP:
        clean_locks(arguments.config_file)
        app = fastapi_app(
            arguments.config_file,
            mount_front=not arguments.no_front,
            auto_upgrade_db=arguments.auto_upgrade_db,
        )[0]
        # noinspection PyTypeChecker
        uvicorn.run(app, host="0.0.0.0", port=8080, log_config=LOGGING_CONFIG)
    else:
        start_all_services(arguments.config_file, [arguments.module])


if __name__ == "__main__":
    main()
