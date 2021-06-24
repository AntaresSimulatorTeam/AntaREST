import argparse
import logging
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Tuple, Any, Optional, Union

import sqlalchemy.ext.baked  # type: ignore
import uvicorn  # type: ignore
from fastapi import FastAPI, HTTPException
from fastapi_jwt_auth import AuthJWT  # type: ignore
from pydantic.main import BaseModel
from sqlalchemy import create_engine
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from antarest import __version__
from antarest.common.config import Config
from antarest.common.persistence import Base
from antarest.common.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.common.utils.web import tags_metadata
from antarest.eventbus.main import build_eventbus
from antarest.launcher.main import build_launcher
from antarest.login.auth import Auth
from antarest.login.main import build_login
from antarest.matrixstore.main import build_matrixstore
from antarest.storage.main import build_storage


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
    return parser.parse_args()


def get_default_config_path() -> Path:
    config = Path("config.yaml")
    if config.exists():
        return config

    config = Path.home() / ".antares/config.yaml"
    if config.exists():
        return config

    raise ValueError(
        "Config file not found. Set it by '-c' with command line or place it at ./config.yaml or ~/.antares/config.yaml"
    )


def get_arguments() -> Tuple[Path, bool, bool]:
    arguments = parse_arguments()

    display_version = arguments.version or False
    if display_version:
        return Path("."), display_version, arguments.no_front

    config_file = Path(arguments.config_file or get_default_config_path())
    return config_file, display_version, arguments.no_front


def get_local_path() -> Path:
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return Path(sys._MEIPASS)  # type: ignore
    except Exception:
        return Path(os.path.abspath(""))


def configure_logger(config: Config) -> None:
    logging_path = config.logging.path
    logging_level = config.logging.level or "INFO"
    logging_format = (
        config.logging.format
        or "%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.basicConfig(
        filename=logging_path, format=logging_format, level=logging_level
    )


class JwtSettings(BaseModel):
    authjwt_secret_key: str
    authjwt_token_location: Tuple[str, ...]
    authjwt_access_token_expires: Union[
        int, timedelta
    ] = Auth.ACCESS_TOKEN_DURATION
    authjwt_refresh_token_expires: Union[
        int, timedelta
    ] = Auth.REFRESH_TOKEN_DURATION
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: Any = {"access", "refresh"}


def fastapi_app(
    config_file: Path,
    resource_path: Optional[Path] = None,
    mount_front: bool = True,
) -> FastAPI:
    res = resource_path or get_local_path() / "resources"
    config = Config.from_yaml_file(res=res, file=config_file)

    configure_logger(config)

    logging.getLogger(__name__).info("Initiating application")

    # Database
    engine = create_engine(
        config.db_url,
        echo=config.debug,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    application = FastAPI(
        title="AntaREST",
        version=__version__,
        docs_url=None,
        openapi_tags=tags_metadata,
    )

    application.add_middleware(
        DBSessionMiddleware,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

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

    @AuthJWT.load_config  # type: ignore
    def get_config() -> JwtSettings:
        return JwtSettings(
            authjwt_secret_key=config.security.jwt_key,
            authjwt_token_location=("headers", "cookies"),
            authjwt_access_token_expires=Auth.ACCESS_TOKEN_DURATION,
            authjwt_refresh_token_expires=Auth.REFRESH_TOKEN_DURATION,
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.on_event("shutdown")
    def shutdown_session() -> None:
        logging.getLogger(__name__).info("Request end")

    @application.exception_handler(HTTPException)
    def handle_http_exception(request: Request, exc: HTTPException) -> Any:
        """Return JSON instead of HTML for HTTP errors."""
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
        return JSONResponse(
            content={
                "description": "Unexpected server error",
                "exception": exc.__class__.__name__,
            },
            status_code=500,
        )

    event_bus = build_eventbus(application, config)
    user_service = build_login(application, config, event_bus=event_bus)
    storage = build_storage(
        application,
        config,
        user_service=user_service,
        event_bus=event_bus,
    )

    build_launcher(
        application,
        config,
        service_storage=storage,
        event_bus=event_bus,
    )

    build_matrixstore(
        application,
        config,
    )

    return application


if __name__ == "__main__":
    config_file, display_version, no_front = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()
    else:
        app = fastapi_app(config_file, mount_front=not no_front)
        uvicorn.run(app, host="0.0.0.0", port=8080)
