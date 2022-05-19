import argparse
import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Tuple, Any, Optional, Dict, cast

import sqlalchemy.ext.baked  # type: ignore
import uvicorn  # type: ignore
from fastapi import FastAPI, HTTPException
from fastapi_jwt_auth import AuthJWT  # type: ignore
from ratelimit import RateLimitMiddleware  # type: ignore
from ratelimit.backends.redis import RedisBackend  # type: ignore
from ratelimit.backends.simple import MemoryBackend  # type: ignore
from sqlalchemy import create_engine
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from antarest import __version__
from antarest.core.cache.main import build_cache
from antarest.core.config import Config
from antarest.core.core_blueprint import create_utils_routes
from antarest.core.exceptions import UnknownModuleError
from antarest.core.filetransfer.main import build_filetransfer_service
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.logging.utils import configure_logger, LoggingMiddleware
from antarest.core.maintenance.main import build_maintenance_manager
from antarest.core.persistence import upgrade_db
from antarest.core.requests import RATE_LIMIT_CONFIG
from antarest.core.swagger import customize_openapi
from antarest.core.tasks.main import build_taskjob_manager
from antarest.core.tasks.service import ITaskService
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
from antarest.login.service import LoginService
from antarest.matrixstore.main import build_matrix_service
from antarest.matrixstore.matrix_garbage_collector import (
    MatrixGarbageCollector,
)
from antarest.matrixstore.service import MatrixService
from antarest.study.main import build_study_service
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.study.web.watcher_blueprint import create_watcher_routes
from antarest.tools.admin_lib import clean_locks
from antarest.worker.archive_worker import ArchiveWorker
from antarest.worker.worker import AbstractWorker

logger = logging.getLogger(__name__)


class Module(str, Enum):
    APP = "app"
    WATCHER = "watcher"
    MATRIX_GC = "matrix_gc"
    ARCHIVE_WORKER = "archive_worker"


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


def get_default_config_path_or_raise() -> Path:
    config_path = get_default_config_path()
    if not config_path:
        raise ValueError(
            "Config file not found. Set it by '-c' with command line or place it at ./config.yaml, ../config.yaml or ~/.antares/config.yaml"
        )
    return config_path


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


def init_db(
    config_file: Path,
    config: Config,
    auto_upgrade_db: bool,
    application: Optional[FastAPI],
) -> None:
    if auto_upgrade_db:
        upgrade_db(config_file)
    connect_args: Dict[str, Any] = {}
    if config.db.db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    else:
        connect_args["connect_timeout"] = config.db.db_connect_timeout

    extra = {}
    if config.db.pool_recycle:
        extra["pool_recycle"] = config.db.pool_recycle

    engine = create_engine(
        config.db.db_url, echo=config.debug, connect_args=connect_args, **extra
    )

    session_args = {
        "autocommit": False,
        "expire_on_commit": False,
        "autoflush": False,
    }
    if application:
        application.add_middleware(
            DBSessionMiddleware,
            custom_engine=engine,
            session_args=session_args,
        )
    else:
        DBSessionMiddleware(
            None, custom_engine=engine, session_args=session_args
        )


def create_core_services(
    application: Optional[FastAPI], config: Config
) -> Tuple[
    ICache,
    IEventBus,
    ITaskService,
    FileTransferManager,
    LoginService,
    MatrixService,
    StudyService,
]:
    redis_client = (
        new_redis_instance(config.redis) if config.redis is not None else None
    )
    event_bus = build_eventbus(application, config, True, redis_client)
    cache = build_cache(config=config, redis_client=redis_client)
    filetransfer_service = build_filetransfer_service(
        application, event_bus, config
    )
    task_service = build_taskjob_manager(application, config, event_bus)
    login_service = build_login(application, config, event_bus=event_bus)
    matrix_service = build_matrix_service(
        application,
        config=config,
        file_transfer_manager=filetransfer_service,
        task_service=task_service,
        user_service=login_service,
        service=None,
    )
    study_service = build_study_service(
        application,
        config,
        matrix_service=matrix_service,
        cache=cache,
        file_transfer_manager=filetransfer_service,
        task_service=task_service,
        user_service=login_service,
        event_bus=event_bus,
    )
    return (
        cache,
        event_bus,
        task_service,
        filetransfer_service,
        login_service,
        matrix_service,
        study_service,
    )


def create_watcher(
    config: Config,
    application: Optional[FastAPI],
    study_service: Optional[StudyService] = None,
) -> Watcher:
    if study_service:
        watcher = Watcher(
            config=config,
            study_service=study_service,
            task_service=study_service.task_service,
        )
    else:
        _, _, task_service, _, _, _, study_service = create_core_services(
            application, config
        )
        watcher = Watcher(
            config=config,
            study_service=study_service,
            task_service=task_service,
        )

    if application:
        application.include_router(
            create_watcher_routes(watcher=watcher, config=config)
        )

    return watcher


def create_matrix_gc(
    config: Config,
    application: Optional[FastAPI],
    study_service: Optional[StudyService] = None,
    matrix_service: Optional[MatrixService] = None,
) -> MatrixGarbageCollector:

    if study_service and matrix_service:
        return MatrixGarbageCollector(
            config=config,
            study_service=study_service,
            matrix_service=matrix_service,
        )
    else:
        _, _, _, _, _, matrix_service, study_service = create_core_services(
            application, config
        )
        return MatrixGarbageCollector(
            config=config,
            study_service=study_service,
            matrix_service=matrix_service,
        )


def create_worker(
    config: Config, event_bus: Optional[IEventBus] = None
) -> AbstractWorker:
    if not event_bus:
        _, event_bus, _, _, _, _, _ = create_core_services(None, config)
    return ArchiveWorker(event_bus, ["archive_test"])


def create_services(
    config: Config, application: Optional[FastAPI], create_all: bool = False
) -> Dict[str, Any]:
    services: Dict[str, Any] = {}

    (
        cache,
        event_bus,
        task_service,
        file_transfer_manager,
        user_service,
        matrix_service,
        study_service,
    ) = create_core_services(application, config)

    maintenance_service = build_maintenance_manager(
        application, config=config, cache=cache, event_bus=event_bus
    )

    launcher = build_launcher(
        application,
        config,
        study_service=study_service,
        event_bus=event_bus,
        task_service=task_service,
        file_transfer_manager=file_transfer_manager,
    )

    watcher = create_watcher(
        config=config, application=application, study_service=study_service
    )

    if (
        config.server.services
        and Module.WATCHER.value in config.server.services
        or create_all
    ):
        services["watcher"] = watcher

    if (
        config.server.services
        and Module.MATRIX_GC.value in config.server.services
        or create_all
    ):
        matrix_garbage_collector = create_matrix_gc(
            config=config,
            application=application,
            study_service=study_service,
            matrix_service=matrix_service,
        )
        services["matrix_gc"] = matrix_garbage_collector

    services["event_bus"] = event_bus
    services["study"] = study_service
    services["launcher"] = launcher
    services["matrix"] = matrix_service
    services["user"] = user_service
    services["cache"] = cache
    services["maintenance"] = maintenance_service
    return services


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
        backend=RedisBackend(config.redis.host, config.redis.port, 1)
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

    customize_openapi(application)
    return application, services


def create_env(config_file: Path) -> Dict[str, Any]:
    """
    Create application services env for testing and scripting purpose
    """
    res = get_local_path() / "resources"
    config = Config.from_yaml_file(res=res, file=config_file)
    configure_logger(config)
    init_db(config_file, config, False, None)
    return create_services(config, None)


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
        elif module == Module.WATCHER:
            res = get_local_path() / "resources"
            config = Config.from_yaml_file(res=res, file=config_file)
            configure_logger(config)
            init_db(config_file, config, False, None)
            watcher = create_watcher(config=config, application=None)
            watcher.start(threaded=False)
        elif module == Module.MATRIX_GC:
            res = get_local_path() / "resources"
            config = Config.from_yaml_file(res=res, file=config_file)
            configure_logger(config)
            init_db(config_file, config, False, None)
            matrix_gc = create_matrix_gc(config=config, application=None)
            matrix_gc.start(threaded=False)
        elif module == Module.ARCHIVE_WORKER:
            res = get_local_path() / "resources"
            config = Config.from_yaml_file(res=res, file=config_file)
            configure_logger(config)
            init_db(config_file, config, False, None)
            worker = create_worker(config)
            worker.start()
        else:
            raise UnknownModuleError(module)
