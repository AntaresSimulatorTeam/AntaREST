import argparse
import logging
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
    task_service = build_taskjob_manager(application, config, event_bus)

    user_service = build_login(application, config, event_bus=event_bus)

    matrix_service = build_matrixstore(application, config, user_service)

    study_service = build_study_service(
        application,
        config,
        matrix_service=matrix_service,
        cache=cache,
        task_service=task_service,
        user_service=user_service,
        event_bus=event_bus,
    )

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

    customize_openapi(application)

    print('----------------KAREMBAAAAAAAAAAAAAAAAAAAAAAAAA')
    with engine.connect() as connexion:
        def convertToUTC(table: str, completion_type: bool = False) -> None:
                to_zone = tz.gettz()
                results = connexion.execute(
                    f"SELECT id, creation_date, completion_date FROM {table}" if completion_type else f"SELECT id, created_at, updated_at FROM {table}")
                for row in results:
                    row_id = row['id']

                    dt_1 = datetime.strptime(row['creation_date' if completion_type else 'created_at'], '%Y-%m-%d %H:%M:%S.%f')
                    dt_1 = dt_1.replace(tzinfo=to_zone)
                    d1 = dt_1.utcfromtimestamp(dt_1.timestamp()).strftime('%Y-%m-%d %H:%M:%S.%f')

                    dt_2 = datetime.strptime(row['completion_date' if completion_type else 'updated_at'], '%Y-%m-%d %H:%M:%S.%f')
                    dt_2 = dt_2.replace(tzinfo=to_zone)
                    d2 = dt_2.utcfromtimestamp(dt_2.timestamp()).strftime('%Y-%m-%d %H:%M:%S.%f')

                    print("CREATED BEFORE: ", row['creation_date' if completion_type else 'created_at'], "; CREATED: ", d1, ";")
                    print("UPDATED BEFORE: ", row['completion_date' if completion_type else 'updated_at'], "; UPDATED: ", d2, ";")
                    if completion_type:
                        print("COMPLETION_TYPE: TRUE")
                        connexion.execute(text(
                            f"UPDATE {table} SET creation_date= :creation_date, completion_date= :completion_date WHERE id='{row_id}'"),
                                          creation_date=d1, completion_date=d2)
                    else:
                        print("COMPLETION_TYPE: FALSE")
                        connexion.execute(text(
                            f"UPDATE {table} SET created_at= :created_at, updated_at= :updated_at WHERE id='{row_id}'"),
                            created_at=d1, updated_at=d2)

        def convertToLocal(table: str, completion_type: bool = False) -> None:
                results = connexion.execute(
                    f"SELECT id, creation_date, completion_date FROM {table}" if completion_type else f"SELECT id, created_at, updated_at FROM {table}")
                for row in results:
                    row_id = row['id']
                    dt_1 = datetime.strptime(row['creation_date' if completion_type else 'created_at'], '%Y-%m-%d %H:%M:%S.%f')
                    dt_1 = dt_1.replace(tzinfo=timezone.utc)
                    dt_1 = datetime.fromtimestamp(dt_1.timestamp())
                    d1 = dt_1.strftime('%Y-%m-%d %H:%M:%S.%f')

                    dt_2 = datetime.strptime(row['completion_date' if completion_type else 'updated_at'], '%Y-%m-%d %H:%M:%S.%f')
                    dt_2 = datetime.replace(tzinfo=timezone.utc)
                    dt_2 = datetime.fromtimestamp(dt_2.timestamp())
                    d2 = dt_2.strftime('%Y-%m-%d %H:%M:%S.%f')

                    print("CREATED BEFORE: ", row['creation_date' if completion_type else 'created_at'], "; CREATED: ", d1, ";")
                    print("UPDATED BEFORE: ", row['completion_date' if completion_type else 'updated_at'], "; UPDATED: ", d2, ";")

                    if completion_type:
                        connexion.execute(text(
                            f"UPDATE {table} SET creation_date= :creation_date, completion_date= :completion_date WHERE id='{row_id}'"),
                                          creation_date=d1, completion_date=d2)
                    else:
                        connexion.execute(text(
                            f"UPDATE {table} SET created_at= :created_at, updated_at= :updated_at WHERE id='{row_id}'"),
                            created_at=d1, updated_at=d2)

        def printAll(table: str, completion_type: bool = False) -> None:
            results = connexion.execute(
                f"SELECT id, creation_date, completion_date FROM {table}" if completion_type else f"SELECT id, created_at, updated_at FROM {table}")
            for row in results:
                print('ID: ', row['id'], "; CREATION: ", row['creation_date' if completion_type else 'created_at'], "; COMPLETION_UPDATED: ", row['completion_date' if completion_type else 'updated_at'])

        print("---- DATETIME: ", datetime.utcnow())
        printAll('study')
        convertToUTC('study')
        #convertToLocal('study')
        #printAll('study')
    print('----------------YEEEEEEEEEEEEESSSSSIIIIIIIIIIIIIIR')

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
