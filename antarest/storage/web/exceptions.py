from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Tuple
from werkzeug import exceptions


class StudyNotFoundError(exceptions.NotFound):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class StudyAlreadyExistError(exceptions.Conflict):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class StudyValidationError(exceptions.UnprocessableEntity):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class StudyTypeUnsupported(exceptions.UnprocessableEntity):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class BadOutputError(exceptions.UnprocessableEntity):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class BadZipBinary(exceptions.UnsupportedMediaType):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class IncorrectPathError(exceptions.NotFound):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class UrlNotMatchJsonDataError(exceptions.NotFound):
    def __init__(self, message: str):
        super().__init__(message)
