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
import contextlib
import logging
import logging.config
import re
import uuid
from contextvars import ContextVar, Token
from typing import Any, Dict, Iterator, Optional, Type

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.login.utils import current_user_context, get_current_user

_request: ContextVar[Optional[Request]] = ContextVar("_request", default=None)
_request_id: ContextVar[Optional[str]] = ContextVar("_request_id", default=None)
_task_id: ContextVar[Optional[str]] = ContextVar("_task_id", default=None)

logger = logging.getLogger(__name__)


class CustomDefaultFormatter(logging.Formatter):
    """
    A custom logging formatter that ensures all fields specified
    in the format string are available in the log record.

    This formatter uses a regular expression pattern to extract
    field names from the format string, and adds any missing
    fields to the log record with a value of `None`.
    """

    @override
    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the specified log record using the custom formatter,
        ensuring all fields specified in the format string are available
        in the record. Returns the formatted string.

        Args:
            record: The logging record to format.

        Returns:
            The formatted message.
        """
        arg_pattern = re.compile(r"%\((\w+)\)")
        arg_names = [x.group(1) for x in arg_pattern.finditer(self._fmt or "")]
        for field in arg_names:
            if field not in record.__dict__:
                record.__dict__[field] = None
        return super().format(record)


def configure_logger(config: Config, handler_cls: str = "logging.FileHandler") -> None:
    """
    Set up the logging configuration based on the input `config` object
    and an optional `handler_cls` argument.

    Args:
        config: A `Config` object that contains the logging configuration parameters.
        handler_cls: A string representing the class of the logging handler.
    """
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "class": "antarest.core.logging.utils.CustomDefaultFormatter",
                "format": (
                    "[%(asctime)s] [%(process)s] [%(name)s]"
                    " - %(trace_id)s"
                    " - %(task_id)s"
                    " - %(threadName)s"
                    " - %(ip)s"
                    " - %(user)s"
                    " - %(levelname)s"
                    " - %(message)s"
                ),
            },
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": (
                    "%(asctime)s"
                    " - %(process)s"
                    " - %(name)s"
                    " - %(trace_id)s"
                    " - %(task_id)s"
                    " - %(threadName)s"
                    " - %(ip)s"
                    " - %(user)s"
                    " - %(levelname)s"
                    " - %(message)s"
                ),
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
        if handler_cls == "logging.FileHandler":
            logging_config["handlers"]["default"] = {
                "class": handler_cls,
                "formatter": "console",
                "level": "INFO",
                "filename": config.logging.logfile,
                "filters": ["context"],
            }
        elif handler_cls == "logging.handlers.TimedRotatingFileHandler":
            # 90 days = 3 months
            # keep only 1 backup (0 means keep all)
            logging_config["handlers"]["default"] = {
                "class": handler_cls,
                "filename": config.logging.logfile,
                "when": "D",
                "interval": 90,
                "backupCount": 1,
                "encoding": "utf-8",
                "delay": False,
                "utc": False,
                "atTime": None,
                "formatter": "console",
                "level": "INFO",
                "filters": ["context"],
            }
        else:  # pragma: no cover
            raise NotImplementedError(handler_cls)

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
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        with RequestContext(request):
            response = await call_next(request)
        return response


class ContextFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool:
        if request := _request.get():
            record.ip = request.scope.get("client", "undefined")[0]
        if request_id := _request_id.get():
            record.trace_id = request_id
        if task_id := _task_id.get():
            record.task_id = task_id
        if current_user := get_current_user():
            record.user = {"id": current_user.id}
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


@contextlib.contextmanager
def task_context(task_id: str, user: Optional[JWTUser]) -> Iterator[None]:
    """
    Sets current user and task_id to specified values.
    """
    with current_user_context(user):
        reset_token = _task_id.set(task_id)
        yield
        _task_id.reset(reset_token)
