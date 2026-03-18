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

import argparse
import copy
import logging
from contextlib import asynccontextmanager
from http import HTTPStatus
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

import pydantic
import uvicorn
import uvicorn.config
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from antarest import __version__
from antarest.core.cli import PathType
from antarest.core.config import Config
from antarest.core.core_blueprint import create_utils_routes
from antarest.core.filesystem_blueprint import create_file_system_blueprint
from antarest.core.filetransfer.web import create_file_transfer_api
from antarest.core.logging.utils import LoggingMiddleware, configure_logger
from antarest.core.maintenance.web import create_maintenance_api
from antarest.core.metrics import add_metrics
from antarest.core.tasks.web import create_tasks_api
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.core.utils.fastapi_sqlalchemy.middleware import init_db_singleton
from antarest.core.utils.utils import get_local_path
from antarest.core.utils.web import tags_metadata
from antarest.dishka_provider import (
    BackgroundServicesProvider,
    ConfigProvider,
    CoreServicesProvider,
    InfrastructureProvider,
)
from antarest.eventbus.web import register_websocket_routes
from antarest.fastapi_jwt_auth.exceptions import AuthJWTException
from antarest.favorite.web import create_favorite_routes
from antarest.front import add_front_app
from antarest.launcher.web import create_launcher_api
from antarest.login.model import init_admin_user
from antarest.login.web import create_login_api, create_user_api
from antarest.matrixstore.web import create_matrix_api
from antarest.output.output_blueprint import create_output_routes
from antarest.service_creator import (
    SESSION_ARGS,
    Module,
    init_db_engine,
)
from antarest.singleton_services import start_all_services
from antarest.study.web.directory_blueprint import create_directory_routes
from antarest.study.web.explorer_blueprint import create_explorer_routes
from antarest.study.web.raw_studies_blueprint import create_raw_study_routes
from antarest.study.web.studies_blueprint import create_study_routes
from antarest.study.web.study_data_blueprint import create_study_data_routes
from antarest.study.web.variant_blueprint import create_study_variant_routes
from antarest.study.web.watcher_blueprint import create_watcher_routes
from antarest.study.web.xpansion_studies_blueprint import create_xpansion_routes
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


def add_exception_handlers(application: FastAPI) -> None:
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

        # Note: we don't log here, because the exception is supposed to be already logged by the logging
        # middleware, with more context
        return JSONResponse(
            content={
                "description": f"Unexpected server error: {exc}",
                "exception": exc.__class__.__name__,
            },
            status_code=500,
        )

    @application.exception_handler(AuthJWTException)
    def authjwt_exception_handler(request: Request, exc: AuthJWTException) -> Any:
        return JSONResponse(
            status_code=HTTPStatus.UNAUTHORIZED,
            content={"detail": exc.message},
        )


def create_routes(api_prefix: str) -> APIRouter:
    """Creates all HTTP and websocket routes.

    Routes use FastAPI's Depends() mechanism for service injection,
    so services don't need to exist yet at registration time.
    """
    api_root = APIRouter(prefix=api_prefix)

    # Utility routes
    api_root.include_router(create_utils_routes())
    api_root.include_router(create_file_system_blueprint())

    # Study routes
    api_root.include_router(create_study_routes())
    api_root.include_router(create_raw_study_routes())
    api_root.include_router(create_study_data_routes())
    api_root.include_router(create_study_variant_routes())
    api_root.include_router(create_xpansion_routes())
    api_root.include_router(create_directory_routes())
    api_root.include_router(create_watcher_routes())
    api_root.include_router(create_explorer_routes())

    # Login routes
    api_root.include_router(create_login_api())
    api_root.include_router(create_user_api())

    # Core service routes
    api_root.include_router(create_tasks_api())
    api_root.include_router(create_file_transfer_api())
    api_root.include_router(create_maintenance_api())

    # Domain service routes
    api_root.include_router(create_matrix_api())
    api_root.include_router(create_launcher_api())
    api_root.include_router(create_output_routes())
    api_root.include_router(create_favorite_routes())

    register_websocket_routes(api_root)

    return api_root


def base_fastapi_app(api_prefix: str, root_path: str) -> FastAPI:
    """
    Creates the fastapi application without injecting services yet.

    Allows in particular to re-use that application object from test to test by swapping
    the services underneath, saving a lot of initialization cost.

    Services are injected in routes using standard FastAPI dependency injection.
    """
    routes = create_routes(api_prefix=api_prefix)

    @asynccontextmanager
    async def set_threadpool_size(app: FastAPI) -> AsyncGenerator[None, None]:
        from anyio import to_thread

        config = app.state.config
        to_thread.current_default_thread_limiter().total_tokens = config.server.worker_threadpool_size

        yield

    application = FastAPI(
        title="AntaREST",
        version=__version__,
        docs_url=None,
        root_path=root_path,
        openapi_tags=tags_metadata,
        lifespan=set_threadpool_size,
        openapi_url=f"{api_prefix}/openapi.json",
        strict_content_type=False,  # Should be removed at some point, required by some known clients for now
    )

    # 2. Database
    application.add_middleware(DBSessionMiddleware)

    # 3. Middlewares
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    add_exception_handlers(application)

    # 4. Include all routes
    application.include_router(routes)

    # It's important to add the logging middleware last, so that any log written or exception thrown
    # by inner middlewares are correctly logged with the context of the request.
    application.add_middleware(LoggingMiddleware)

    return application


def init_db(config: Config, config_file: Path, auto_upgrade: bool, init_admin: bool) -> None:
    """
    Creates the DB engine, sets it for use by the application, and initializes the scehma and admin user if needed.
    """
    engine = init_db_engine(config, auto_upgrade, config_file=config_file)
    init_db_singleton(custom_engine=engine, session_args=SESSION_ARGS)
    if init_admin:
        init_admin_user(engine, SESSION_ARGS, config.security.admin_pwd)


def inject_services(app: FastAPI, config: Config) -> None:
    """
    Inject services into the application state, so that they can be accessed from routes.

    Sets up the dishka dependency injection container and attaches it to the FastAPI app.
    """
    import asyncio

    from dishka import AsyncContainer, make_async_container
    from dishka.integrations.fastapi import setup_dishka

    # Close previous container if re-injecting (e.g. in tests)
    old_container: AsyncContainer | None = getattr(app.state, "dishka_container", None)
    if old_container is not None:
        try:
            loop = asyncio.get_running_loop()
            loop.run_until_complete(old_container.close())
        except RuntimeError:
            asyncio.run(old_container.close())

    container = make_async_container(
        ConfigProvider(config),
        InfrastructureProvider(),
        CoreServicesProvider(),
        BackgroundServicesProvider(),
    )

    if old_container is not None:
        # Middleware was already added on the first call; just swap the container reference
        app.state.dishka_container = container
    else:
        setup_dishka(container, app)

    # Store config on app.state for the lifespan handler (threadpool size)
    app.state.config = config

    # Eagerly resolve OutputService to trigger the register_output_access side effect
    # (StudyService <-> OutputService wiring). Dishka is lazy by default.
    async def _eager_init() -> None:
        from antarest.output.output_service import OutputService

        await container.get(OutputService)

    try:
        loop = asyncio.get_running_loop()
        loop.run_until_complete(_eager_init())
    except RuntimeError:
        asyncio.run(_eager_init())


def fastapi_app(
    config_file: Path,
    resource_path: Optional[Path] = None,
    mount_front: bool = True,
    auto_upgrade_db: bool = False,
) -> FastAPI:
    res = resource_path or get_local_path() / "resources"
    config = Config.from_yaml_file(res=res, file=config_file)

    configure_logger(config)

    logger.info("Initiating application")

    app = base_fastapi_app(config.api_prefix, config.root_path)

    init_db(config, config_file, auto_upgrade_db, init_admin=True)

    inject_services(app, config)

    add_metrics(app, config)

    if mount_front:
        add_front_app(app, res, config.api_prefix)
    else:
        # noinspection PyUnusedLocal
        @app.get("/", include_in_schema=False)
        def home(request: Request) -> Any:
            return ""

    return app


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
        )
        # noinspection PyTypeChecker
        uvicorn.run(app, host="0.0.0.0", port=8080, log_config=LOGGING_CONFIG)
    else:
        start_all_services(arguments.config_file, [arguments.module])


if __name__ == "__main__":
    main()
