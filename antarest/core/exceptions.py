from http import HTTPStatus
from typing import Optional

from fastapi import HTTPException


class ShouldNotHappenException(Exception):
    pass


class UnknownModuleError(Exception):
    def __init__(self, message: str) -> None:
        super(UnknownModuleError, self).__init__(message)


class StudyNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class VariantGenerationError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.EXPECTATION_FAILED, message)


class NoParentStudyError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class CommandNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class CommandNotValid(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.EXPECTATION_FAILED, message)


class CommandApplicationError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.INTERNAL_SERVER_ERROR, message)


class CommandUpdateAuthorizationError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.LOCKED, message)


class StudyAlreadyExistError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.CONFLICT, message)


class StudyValidationError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class VariantStudyParentNotValid(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class StudyTypeUnsupported(HTTPException):
    def __init__(self, uuid: str, type: str) -> None:
        super().__init__(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            f"Study {uuid} with type {type} not recognized",
        )


class NotAManagedStudyException(HTTPException):
    def __init__(self, uuid: str) -> None:
        super().__init__(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            f"Study {uuid} is not managed",
        )


class StudyDeletionNotAllowed(HTTPException):
    def __init__(self, uuid: str, message: Optional[str] = None) -> None:
        msg = f"Study {uuid} (not managed) is not allowed to be deleted"
        if message:
            msg += f"\n{msg}"
        super().__init__(
            HTTPStatus.FORBIDDEN,
            msg,
        )


class UnsupportedStudyVersion(HTTPException):
    def __init__(self, version: str) -> None:
        super().__init__(
            HTTPStatus.BAD_REQUEST,
            f"Study version {version} is not supported",
        )


class UnsupportedOperationOnArchivedStudy(HTTPException):
    def __init__(self, uuid: str) -> None:
        super().__init__(
            HTTPStatus.BAD_REQUEST,
            f"Study {uuid} is archived",
        )


class BadOutputError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class BadZipBinary(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, message)


class IncorrectPathError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class UrlNotMatchJsonDataError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class StudyOutputNotFoundError(Exception):
    pass
