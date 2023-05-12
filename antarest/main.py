import argparse
import copy
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, cast

import sqlalchemy.ext.baked  # type: ignore
import uvicorn  # type: ignore
import uvicorn.config  # type: ignore
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
from antarest.core.logging.utils import LoggingMiddleware, configure_logger
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
from antarest.utils import Module, create_services, init_db

logger = logging.getLogger(__name__)


class PathType:
    """file or directory path type for `argparse` parser

    The `PathType` class represents a type of argument that can be used
    with the `argparse` library.
    This class takes three boolean arguments, `exists`, `file_ok`, and `dir_ok`,
    which specify whether the path argument must exist, whether it can be a file,
    and whether it can be a directory, respectively.

    Example Usage:

    ```python
    import argparse
    from antarest.main import PathType

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=PathType(file_ok=True, exists=True))
    args = parser.parse_args()

    print(args.input)
    ```

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
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

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


LOGGING_CONFIG = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
LOGGING_CONFIG["formatters"]["default"]["fmt"] = (
    # fmt: off
    "[%(asctime)s] [%(process)s]"
    " %(levelprefix)s"
    "  %(message)s"
    # fmt: on
)
LOGGING_CONFIG["formatters"]["access"]["fmt"] = (
    # fmt: off
    "[%(asctime)s] [%(process)s] [%(name)s]"
    " %(levelprefix)s"
    " %(client_addr)s - \"%(request_line)s\""
    " %(status_code)s"
    # fmt: on
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
        services = SingletonServices(arguments.config_file, [arguments.module])
        services.start()


if __name__ == "__main__":
    main()
