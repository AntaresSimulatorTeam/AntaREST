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

import argparse
import copy
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional, Tuple, cast

import pydantic
import uvicorn
import uvicorn.config
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from ratelimit import RateLimitMiddleware  # type: ignore
from ratelimit.backends.redis import RedisBackend  # type: ignore
from ratelimit.backends.simple import MemoryBackend  # type: ignore
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from antarest import __version__
from antarest.core.application import AppBuildContext
from antarest.core.cli import PathType
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
from antarest.front import add_front_app
from antarest.login.auth import Auth, JwtSettings
from antarest.login.model import init_admin_user
from antarest.service_creator import SESSION_ARGS, Module, Services, create_services, init_db_engine
from antarest.singleton_services import start_all_services
from antarest.tools.admin_lib import clean_locks

logger = logging.getLogger(__name__)


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


def fastapi_app(
    config_file: Path,
    resource_path: Optional[Path] = None,
    mount_front: bool = True,
    auto_upgrade_db: bool = False,
) -> Tuple[FastAPI, Services]:
    res = resource_path or get_local_path() / "resources"
    config = Config.from_yaml_file(res=res, file=config_file)
    configure_logger(config)

    logger.info("Initiating application")

    @asynccontextmanager
    async def set_default_executor(app: FastAPI) -> AsyncGenerator[None, None]:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        loop = asyncio.get_running_loop()
        loop.set_default_executor(ThreadPoolExecutor(max_workers=config.server.worker_threadpool_size))
        yield

    application = FastAPI(
        title="AntaREST",
        version=__version__,
        docs_url=None,
        root_path=config.root_path,
        openapi_tags=tags_metadata,
        lifespan=set_default_executor,
        openapi_url=f"{config.api_prefix}/openapi.json",
    )

    api_root = APIRouter(prefix=config.api_prefix)

    app_ctxt = AppBuildContext(application, api_root)

    # Database
    engine = init_db_engine(config_file, config, auto_upgrade_db)
    application.add_middleware(DBSessionMiddleware, custom_engine=engine, session_args=SESSION_ARGS)
    # Since Starlette Version 0.24.0, the middlewares are lazily built inside this function
    # But we need to instantiate this middleware as it's needed for the study service.
    # So we manually instantiate it here.
    DBSessionMiddleware(None, custom_engine=engine, session_args=cast(Dict[str, bool], SESSION_ARGS))

    application.add_middleware(LoggingMiddleware)

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
    api_root.include_router(create_utils_routes(config))
    api_root.include_router(create_file_system_blueprint(config))

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
    services = create_services(config, app_ctxt)

    application.include_router(api_root)

    if services.watcher and not config.desktop_mode:
        services.watcher.start()

    if services.matrix_gc:
        services.matrix_gc.start()

    if services.auto_archiver:
        services.auto_archiver.start()

    customize_openapi(application)

    if mount_front:
        add_front_app(application, res, config.api_prefix)
    else:
        # noinspection PyUnusedLocal
        @application.get("/", include_in_schema=False)
        def home(request: Request) -> Any:
            return ""

    cancel_orphan_tasks(engine=engine, session_args=SESSION_ARGS)
    return application, services


LOGGING_CONFIG = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
# noinspection SpellCheckingInspection
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "[%(asctime)s] [%(process)s] %(levelprefix)s  %(message)s"
# noinspection SpellCheckingInspection
LOGGING_CONFIG["formatters"]["access"]["fmt"] = (
    '[%(asctime)s] [%(process)s] [%(name)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
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
