import argparse
import logging
import os
import sys
from datetime import timezone, datetime
from pathlib import Path
from typing import Tuple, Any, Optional, Dict

import sqlalchemy.ext.baked  # type: ignore
import uvicorn  # type: ignore
from dateutil import tz
from fastapi import FastAPI, HTTPException
from fastapi_jwt_auth import AuthJWT  # type: ignore
from sqlalchemy import create_engine, text
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from antarest import __version__
from antarest.core.cache.main import build_cache
from antarest.core.config import Config
from antarest.core.core_blueprint import create_utils_routes
from antarest.core.filetransfer.main import build_filetransfer_service
from antarest.core.filetransfer.web import create_file_transfer_api
from antarest.core.logging.utils import configure_logger, LoggingMiddleware
from antarest.core.persistence import upgrade_db
from antarest.core.swagger import customize_openapi
from antarest.core.tasks.main import build_taskjob_manager
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.core.utils.utils import (
    get_default_config_path,
    get_local_path,
    new_redis_instance,
)
from antarest.core.utils.web import tags_metadata
from antarest.eventbus.main import build_eventbus
from antarest.launcher.main import build_launcher
from antarest.login.auth import Auth, JwtSettings
from antarest.login.main import build_login
from antarest.matrixstore.main import build_matrixstore
from antarest.study.main import build_study_service
from antarest.study.storage.rawstudy.watcher import Watcher

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
    return parser.parse_args()


def get_default_config_path_or_raise() -> Path:
    config_path = get_default_config_path()
    if not config_path:
        raise ValueError(
            "Config file not found. Set it by '-c' with command line or place it at ./config.yaml or ~/.antares/config.yaml"
        )
    return config_path


def get_arguments() -> Tuple[Path, bool, bool, bool]:
    arguments = parse_arguments()

    display_version = arguments.version or False
    if display_version:
        return (
            Path("."),
            display_version,
            arguments.no_front,
            arguments.auto_upgrade_db,
        )

    config_file = Path(
        arguments.config_file or get_default_config_path_or_raise()
    )
    return (
        config_file,
        display_version,
        arguments.no_front,
        arguments.auto_upgrade_db,
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

    # Database
    if auto_upgrade_db:
        upgrade_db(config_file)
    connect_args = {}
    if config.db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        config.db_url,
        echo=config.debug,
        connect_args=connect_args,
    )

    application = FastAPI(
        title="AntaREST",
        version=__version__,
        docs_url=None,
        root_path=config.root_path,
        openapi_tags=tags_metadata,
    )

    application.add_middleware(
        DBSessionMiddleware,
        custom_engine=engine,
        session_args={
            "autocommit": False,
            "expire_on_commit": False,
            "autoflush": False,
        },
    )

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

    services: Dict[str, Any] = {}

    redis_client = (
        new_redis_instance(config.redis) if config.redis is not None else None
    )
    event_bus = build_eventbus(application, config, True, redis_client)
    cache = build_cache(config=config, redis_client=redis_client)

    filetransfer_service = build_filetransfer_service(
        application, event_bus, config
    )
    task_service = build_taskjob_manager(application, config, event_bus)

    user_service = build_login(application, config, event_bus=event_bus)

    matrix_service = build_matrixstore(application, config, user_service)

    study_service = build_study_service(
        application,
        config,
        matrix_service=matrix_service,
        cache=cache,
        file_transfer_manager=filetransfer_service,
        task_service=task_service,
        user_service=user_service,
        event_bus=event_bus,
    )
    watcher = Watcher(config=config, service=study_service)
    watcher.start()

    launcher = build_launcher(
        application,
        config,
        study_service=study_service,
        event_bus=event_bus,
    )

    services["event_bus"] = event_bus
    services["study"] = study_service
    services["launcher"] = launcher
    services["matrix"] = matrix_service
    services["user"] = user_service
    services["cache"] = cache
    services["watcher"] = watcher

    customize_openapi(application)
    return application, services


if __name__ == "__main__":
    config_file, display_version, no_front, auto_upgrade_db = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()
    else:
        app, _ = fastapi_app(
            config_file,
            mount_front=not no_front,
            auto_upgrade_db=auto_upgrade_db,
        )
        uvicorn.run(app, host="0.0.0.0", port=8080)
