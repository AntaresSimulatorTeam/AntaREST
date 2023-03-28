from http import HTTPStatus
from typing import Optional, Set

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
    def __init__(self, uuid: str, type_: str) -> None:
        super().__init__(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            f"Study {uuid} with type {type_} not recognized",
        )


class NotAManagedStudyException(HTTPException):
    def __init__(self, uuid: str) -> None:
        super().__init__(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            f"Study {uuid} is not managed",
        )


class TaskAlreadyRunning(HTTPException):
    def __init__(self) -> None:
        super(TaskAlreadyRunning, self).__init__(
            HTTPStatus.EXPECTATION_FAILED, "Task is already running"
        )


class StudyDeletionNotAllowed(HTTPException):
    def __init__(self, uuid: str, message: Optional[str] = None) -> None:
        msg = f"Study {uuid} (not managed) is not allowed to be deleted"
        if message:
            msg += f"\n{message}"
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


class WritingInsideZippedFileException(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class NoBindingConstraintError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class NoConstraintError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class ConstraintAlreadyExistError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class MissingDataError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class ConstraintIdNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class LayerNotFound(HTTPException):
    def __init__(self) -> None:
        super().__init__(HTTPStatus.NOT_FOUND)


class LayerNotAllowedToBeDeleted(HTTPException):
    def __init__(self) -> None:
        super().__init__(HTTPStatus.EXPECTATION_FAILED)


class StudyOutputNotFoundError(Exception):
    pass


class AreaNotFound(HTTPException):
    def __init__(self, *area_ids: str) -> None:
        count = len(area_ids)
        ids = ", ".join(f"'{a}'" for a in area_ids)
        msg = {
            0: "All areas are found",
            1: f"{count} area is not found: {ids}",
            2: f"{count} areas are not found: {ids}",
        }[min(count, 2)]
        super().__init__(HTTPStatus.NOT_FOUND, msg)


class DistrictNotFound(HTTPException):
    def __init__(self, *district_ids: str) -> None:
        count = len(district_ids)
        ids = ", ".join(f"'{a}'" for a in district_ids)
        msg = {
            0: "All districts are found",
            1: f"{count} district is not found: {ids}",
            2: f"{count} districts are not found: {ids}",
        }[min(count, 2)]
        super().__init__(HTTPStatus.NOT_FOUND, msg)


class DistrictAlreadyExist(HTTPException):
    def __init__(self, *district_ids: str):
        count = len(district_ids)
        ids = ", ".join(f"'{a}'" for a in district_ids)
        msg = {
            0: "No district already exist",
            1: f"{count} district already exist: {ids}",
            2: f"{count} districts already exist: {ids}",
        }[min(count, 2)]
        super().__init__(HTTPStatus.CONFLICT, msg)


class AllocationDataNotFound(HTTPException):
    def __init__(self, area_id: str):
        msg = f"No allocation data found for area {area_id}"
        super().__init__(HTTPStatus.NOT_FOUND, msg)


class InvalidAllocationData(HTTPException):
    def __init__(self, invalid_ids: Set[str]):
        msg = f"Invalid areas: {', '.join(invalid_ids)}"
        super().__init__(HTTPStatus.BAD_REQUEST, msg)


class BadEditInstructionException(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class CannotScanInternalWorkspace(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            HTTPStatus.BAD_REQUEST,
            "You cannot scan the default internal workspace",
        )
