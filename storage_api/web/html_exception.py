from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Tuple


class HtmlException(Exception):
    def __init__(self, message: str, html_code_error: int):
        self.message = message
        self.html_code_error = html_code_error


def stop_and_return_on_html_exception(
    func: Callable[..., Tuple[Any, int]]
) -> Callable[..., Any]:
    @wraps(func)
    def catch_and_return_html_exception(*args: str, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except HtmlException as e:
            return e.message, e.html_code_error

    return catch_and_return_html_exception


class StudyNotFoundError(HtmlException):
    def __init__(self, message: str) -> None:
        super().__init__(message, HTTPStatus.NOT_FOUND)


class StudyAlreadyExistError(HtmlException):
    def __init__(self, message: str) -> None:
        super().__init__(message, HTTPStatus.CONFLICT)


class StudyValidationError(HtmlException):
    def __init__(self, message: str) -> None:
        super().__init__(message, HTTPStatus.UNPROCESSABLE_ENTITY)


class BadZipBinary(HtmlException):
    def __init__(self, message: str) -> None:
        super().__init__(message, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)


class IncorrectPathError(HtmlException):
    def __init__(self, message: str) -> None:
        super().__init__(message, HTTPStatus.NOT_FOUND)


class UrlNotMatchJsonDataError(HtmlException):
    def __init__(self, message: str):
        super(UrlNotMatchJsonDataError, self).__init__(message, 404)
