from http import HTTPStatus
from typing import Optional

from fastapi.exceptions import HTTPException


class ShouldNotHappenException(Exception):
    pass


class STStorageFieldsNotFoundError(HTTPException):
    """Fields of the short-term storage are not found"""

    def __init__(self, storage_id: str) -> None:
        detail = f"Fields of storage '{storage_id}' not found"
        super().__init__(HTTPStatus.NOT_FOUND, detail)

    def __str__(self) -> str:
        return self.detail


class STStorageMatrixNotFoundError(HTTPException):
    """Matrix of the short-term storage is not found"""

    def __init__(self, study_id: str, area_id: str, storage_id: str, ts_name: str) -> None:
        detail = f"Time series '{ts_name}' of storage '{storage_id}' not found"
        super().__init__(HTTPStatus.NOT_FOUND, detail)

    def __str__(self) -> str:
        return self.detail


class STStorageConfigNotFoundError(HTTPException):
    """Configuration for short-term storage is not found"""

    def __init__(self, study_id: str, area_id: str) -> None:
        detail = f"The short-term storage configuration of area '{area_id}' not found"
        super().__init__(HTTPStatus.NOT_FOUND, detail)

    def __str__(self) -> str:
        return self.detail


class STStorageNotFoundError(HTTPException):
    """Short-term storage is not found"""

    def __init__(self, study_id: str, area_id: str, st_storage_id: str) -> None:
        detail = f"Short-term storage '{st_storage_id}' not found in area '{area_id}'"
        super().__init__(HTTPStatus.NOT_FOUND, detail)

    def __str__(self) -> str:
        return self.detail


class DuplicateSTStorageId(HTTPException):
    """Exception raised when trying to create a short-term storage with an already existing id."""

    def __init__(self, study_id: str, area_id: str, st_storage_id: str) -> None:
        detail = f"Short term storage '{st_storage_id}' already exists in area '{area_id}'"
        super().__init__(HTTPStatus.CONFLICT, detail)

    def __str__(self) -> str:
        return self.detail


class UnknownModuleError(Exception):
    def __init__(self, message: str) -> None:
        super(UnknownModuleError, self).__init__(message)


class StudyNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class VariantGenerationError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.EXPECTATION_FAILED, message)


class VariantGenerationTimeoutError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.REQUEST_TIMEOUT, message)


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
        super(TaskAlreadyRunning, self).__init__(HTTPStatus.EXPECTATION_FAILED, "Task is already running")


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


class BindingConstraintNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class NoConstraintError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class ConstraintAlreadyExistError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class DuplicateConstraintName(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.CONFLICT, message)


class InvalidConstraintName(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class InvalidFieldForVersionError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class IncoherenceBetweenMatricesLength(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class MissingDataError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class ConstraintIdNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class LayerNotFound(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            HTTPStatus.NOT_FOUND,
            "Layer not found",
        )


class LayerNotAllowedToBeDeleted(HTTPException):
    def __init__(self, layer_name: str = "All") -> None:
        super().__init__(
            HTTPStatus.BAD_REQUEST,
            f"You cannot delete the layer: '{layer_name}'",
        )


class StudyOutputNotFoundError(Exception):
    pass


class AllocationDataNotFound(HTTPException):
    def __init__(self, *area_ids: str) -> None:
        count = len(area_ids)
        ids = ", ".join(f"'{a}'" for a in area_ids)
        msg = {
            0: "Allocation data is found",
            1: f"Allocation data for area {ids} is not found",
            2: f"Allocation data for areas {ids} is not found",
        }[min(count, 2)]
        super().__init__(HTTPStatus.NOT_FOUND, msg)


class AreaNotFound(HTTPException):
    def __init__(self, *area_ids: str) -> None:
        count = len(area_ids)
        ids = ", ".join(f"'{a}'" for a in area_ids)
        msg = {
            0: "All areas are found",
            1: f"Area is not found: {ids}",
            2: f"Areas are not found: {ids}",
        }[min(count, 2)]
        super().__init__(HTTPStatus.NOT_FOUND, msg)


class DuplicateAreaName(HTTPException):
    """Exception raised when trying to create an area with an already existing name."""

    def __init__(self, area_name: str) -> None:
        msg = f"Area '{area_name}' already exists and could not be created"
        super().__init__(HTTPStatus.CONFLICT, msg)


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


class BadEditInstructionException(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class CannotScanInternalWorkspace(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            HTTPStatus.BAD_REQUEST,
            "You cannot scan the default internal workspace",
        )


class ClusterNotFound(HTTPException):
    def __init__(self, cluster_id: str) -> None:
        super().__init__(
            HTTPStatus.NOT_FOUND,
            f"Cluster: '{cluster_id}' not found",
        )


class ClusterConfigNotFound(HTTPException):
    def __init__(self, area_id: str) -> None:
        super().__init__(
            HTTPStatus.NOT_FOUND,
            f"Cluster configuration for area: '{area_id}' not found",
        )


class ClusterAlreadyExists(HTTPException):
    """Exception raised when attempting to create a cluster with an already existing ID."""

    def __init__(self, cluster_type: str, cluster_id: str) -> None:
        super().__init__(
            HTTPStatus.CONFLICT,
            f"{cluster_type} cluster with ID '{cluster_id}' already exists and could not be created.",
        )
