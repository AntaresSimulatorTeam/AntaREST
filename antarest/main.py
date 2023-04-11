import argparse
import logging
import sys
from pathlib import Path
from typing import Tuple, Any, Optional, Dict, cast

import sqlalchemy.ext.baked  # type: ignore
import uvicorn  # type: ignore
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi_jwt_auth import AuthJWT  # type: ignore
from ratelimit import RateLimitMiddleware  # type: ignore
from ratelimit.backends.redis import RedisBackend  # type: ignore
from ratelimit.backends.simple import MemoryBackend  # type: ignore
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from antarest import __version__
from antarest.core.config import Config
from antarest.core.core_blueprint import create_utils_routes
from antarest.core.logging.utils import configure_logger, LoggingMiddleware
from antarest.core.requests import RATE_LIMIT_CONFIG
from antarest.core.swagger import customize_openapi
from antarest.core.utils.utils import get_local_path
from antarest.core.utils.web import tags_metadata
from antarest.login.auth import Auth, JwtSettings
from antarest.matrixstore.matrix_garbage_collector import (
    MatrixGarbageCollector,
)
from antarest.singleton_services import SingletonServices
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.tools.admin_lib import clean_locks
from antarest.utils import (
    Module,
    get_default_config_path_or_raise,
    init_db,
    create_services,
)

logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        help="path to the config file",
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        help="Server version",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--no-front",
        dest="no_front",
        help="Not embed the front build",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--auto-upgrade-db",
        dest="auto_upgrade_db",
        help="Automatically upgrade db",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--module",
        dest="module",
        help="Select a module to run (default is the application server)",
        choices=[mod.value for mod in Module],
        action="store",
        default=Module.APP.value,
        required=False,
    )
    return parser.parse_args()


def get_arguments() -> Tuple[Path, bool, bool, bool, Module]:
    arguments = parse_arguments()

    display_version = arguments.version or False
    if display_version:
        return (
            Path("."),
            display_version,
            arguments.no_front,
            arguments.auto_upgrade_db,
            Module.APP,
        )

    config_file = Path(
        arguments.config_file or get_default_config_path_or_raise()
    )
    return (
        config_file,
        display_version,
        arguments.no_front,
        arguments.auto_upgrade_db,
        Module(arguments.module),
    )


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
    init_db(config_file, config, auto_upgrade_db, application)

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
            """
            Home ui
            ---
            responses:
                '200':
                  content:
                     application/html: {}
                  description: html home page
            tags:
              - UI
            """
            return templates.TemplateResponse(
                "index.html", {"request": request}
            )

    else:

        @application.get("/", include_in_schema=False)
        def home(request: Request) -> Any:
            """
            Home ui
            ---
            responses:
                '200':
                  content:
                     application/html: {}
                  description: html home page
            tags:
              - UI
            """
            return ""

    @application.on_event("startup")
    def set_default_executor() -> None:
        from concurrent.futures import ThreadPoolExecutor
        import asyncio

        loop = asyncio.get_running_loop()
        loop.set_default_executor(
            ThreadPoolExecutor(
                max_workers=config.server.worker_threadpool_size
            )
        )

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

    @application.exception_handler(HTTPException)
    def handle_http_exception(request: Request, exc: HTTPException) -> Any:
        """Return JSON instead of HTML for HTTP errors."""
        logger.error("HTTP Exception", exc_info=exc)
        return JSONResponse(
            content={
                "description": exc.detail,
                "exception": exc.__class__.__name__,
            },
            status_code=exc.status_code,
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request, exc: RequestValidationError
    ) -> Any:
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

    @application.exception_handler(Exception)
    def handle_all_exception(request: Request, exc: Exception) -> Any:
        """Return JSON instead of HTML for HTTP errors."""
        logger.error("Unexpected Exception", exc_info=exc)
        return JSONResponse(
            content={
                "description": "Unexpected server error",
                "exception": exc.__class__.__name__,
            },
            status_code=500,
        )

    # rate limiter
    auth_manager = Auth(config)
    application.add_middleware(
        RateLimitMiddleware,
        authenticate=auth_manager.create_auth_function(),
        backend=RedisBackend(
            config.redis.host, config.redis.port, 1, config.redis.password
        )
        if config.redis is not None
        else MemoryBackend(),
        config=RATE_LIMIT_CONFIG,
    )

    services = create_services(config, application)

    if (
        config.server.services
        and Module.WATCHER.value in config.server.services
    ):
        watcher = cast(Watcher, services["watcher"])
        watcher.start()

    if (
        config.server.services
        and Module.MATRIX_GC.value in config.server.services
    ):
        matrix_gc = cast(MatrixGarbageCollector, services["matrix_gc"])
        matrix_gc.start()

    if (
        config.server.services
        and Module.AUTO_ARCHIVER.value in config.server.services
    ):
        auto_archiver = cast(AutoArchiveService, services["auto_archiver"])
        auto_archiver.start()

    customize_openapi(application)
    return application, services


if __name__ == "__main__":
    (
        config_file,
        display_version,
        no_front,
        auto_upgrade_db,
        module,
    ) = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()
    else:
        if module == Module.APP:
            clean_locks(config_file)
            app, _ = fastapi_app(
                config_file,
                mount_front=not no_front,
                auto_upgrade_db=auto_upgrade_db,
            )
            uvicorn.run(app, host="0.0.0.0", port=8080)
        else:
            services = SingletonServices(config_file, [module])
            services.start()
