import logging
import logging.config
import os
import re
import uuid
from pythonjsonlogger.jsonlogger import JsonFormatter
from contextvars import ContextVar, Token
from typing import Optional, Type, Any, Dict

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from antarest.core.config import Config

_request: ContextVar[Optional[Request]] = ContextVar("_request", default=None)
_request_id: ContextVar[Optional[str]] = ContextVar(
    "_request_id", default=None
)

logger = logging.getLogger(__name__)


class CustomDefaultFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        arg_pattern = re.compile(r"%\((\w+)\)")
        arg_names = [x.group(1) for x in arg_pattern.finditer(self._fmt or "")]
        for field in arg_names:
            if field not in record.__dict__:
                record.__dict__[field] = None
        return super().format(record)


def configure_logger(config: Config) -> None:
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "class": "antarest.core.logging.utils.CustomDefaultFormatter",
                "format": "%(asctime)s - %(trace_id)s - %(threadName)s - %(name)s - %(ip)s - %(user)s - %(pid)s - %(levelname)s - %(message)s",
            },
            "json": {
                "class": f"{JsonFormatter.__module__}.{JsonFormatter.__name__}",
                "format": "%(asctime)s - %(trace_id)s - %(threadName)s - %(name)s - %(ip)s - %(user)s - %(pid)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "console",
                "level": "INFO",
                "stream": "ext://sys.stdout",
                "filters": ["context"],
            },
        },
        "filters": {
            "context": {
                "()": "antarest.core.logging.utils.ContextFilter",
            }
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["default"],
                "level": "INFO",
                "propagate": True,
            },
            "antarest.study.storage.rawstudy.watcher": {
                "handlers": ["default"],
                "level": "WARN",
                "propagate": True,
            },
        },
    }
    if config.logging.logfile is not None:
        logging_config["handlers"]["default"] = {
            "class": "logging.FileHandler",
            "formatter": "console",
            "level": "INFO",
            "filename": config.logging.logfile,
            "filters": ["context"],
        }
    if config.logging.level is not None and config.logging.level in [
        "INFO",
        "WARNING",
        "ERROR",
        "DEBUG",
    ]:
        logging_config["loggers"][""]["level"] = config.logging.level
    if config.logging.json:
        logging_config["handlers"]["default"]["formatter"] = "json"

    logging.config.dictConfig(logging_config)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        with RequestContext(request):
            response = await call_next(request)
        return response


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request: Optional[Request] = _request.get()
        request_id: Optional[str] = _request_id.get()
        if request is not None:
            record.ip = request.scope.get("client", ("undefined"))[0]
        record.trace_id = request_id
        record.pid = os.getpid()
        return True


class RequestContext:
    def __init__(
        self,
        request: Request,
    ) -> None:
        self.request_token: Optional[Token[Optional[Any]]] = None
        self.request_id_token: Optional[Token[Optional[Any]]] = None
        self.request = request

    def __enter__(self) -> Type["RequestContext"]:
        self.request_token = _request.set(self.request)
        self.request_id_token = _request_id.set(str(uuid.uuid4()))
        return type(self)

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if self.request_token is not None:
            _request.reset(self.request_token)
        if self.request_id_token is not None:
            _request_id.reset(self.request_id_token)


context_filter = ContextFilter()
