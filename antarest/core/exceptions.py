import re
import typing as t
from http import HTTPStatus

from fastapi.exceptions import HTTPException


class ShouldNotHappenException(Exception):
    pass


# ============================================================
# Exceptions related to the study configuration (`.ini` files)
# ============================================================

# Naming convention for exceptions related to the study configuration:
#
# | Topic         | NotFound (404)        | Duplicate (409)        | Invalid (422)        |
# |---------------|-----------------------|------------------------|----------------------|
# | ConfigFile    | ConfigFileNotFound    | N/A                    | InvalidConfigFile    |
# | ConfigSection | ConfigSectionNotFound | DuplicateConfigSection | InvalidConfigSection |
# | ConfigOption  | ConfigOptionNotFound  | DuplicateConfigOption  | InvalidConfigOption  |
# | Matrix        | MatrixNotFound        | DuplicateMatrix        | InvalidMatrix        |


THERMAL_CLUSTER = "thermal cluster"
RENEWABLE_CLUSTER = "renewable cluster"
SHORT_TERM_STORAGE = "short-term storage"

# ============================================================
# NotFound (404)
# ============================================================

_match_input_path = re.compile(r"input(?:/[\w*-]+)+").fullmatch


class ConfigFileNotFound(HTTPException):
    """
    Exception raised when a configuration file is not found (404 Not Found).

    Notes:
        The study ID is not provided because it is implicit.

    Attributes:
        path: Path of the missing file(s) relative to the study directory.
        area_ids: Sequence of area IDs for which the file(s) is/are missing.
    """

    object_name = ""
    """Name of the object that is not found: thermal, renewables, etc."""

    def __init__(self, path: str, *area_ids: str):
        assert _match_input_path(path), f"Invalid path: '{path}'"
        self.path = path
        self.area_ids = area_ids
        ids = ", ".join(f"'{a}'" for a in area_ids)
        detail = {
            0: f"Path '{path}' not found",
            1: f"Path '{path}' not found for area {ids}",
            2: f"Path '{path}' not found for areas {ids}",
        }[min(len(area_ids), 2)]
        if self.object_name:
            detail = f"{self.object_name.title()} {detail}"
        super().__init__(HTTPStatus.NOT_FOUND, detail)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail


class ThermalClusterConfigNotFound(ConfigFileNotFound):
    """Configuration for thermal cluster is not found (404 Not Found)"""

    object_name = THERMAL_CLUSTER


class RenewableClusterConfigNotFound(ConfigFileNotFound):
    """Configuration for renewable cluster is not found (404 Not Found)"""

    object_name = RENEWABLE_CLUSTER


class STStorageConfigNotFound(ConfigFileNotFound):
    """Configuration for short-term storage is not found (404 Not Found)"""

    object_name = SHORT_TERM_STORAGE


class ConfigSectionNotFound(HTTPException):
    """
    Exception raised when a configuration section is not found (404 Not Found).

    Notes:
        The study ID is not provided because it is implicit.

    Attributes:
        path: Path of the missing file(s) relative to the study directory.
        section_id: ID of the missing section.
    """

    object_name = ""
    """Name of the object that is not found: thermal, renewables, etc."""

    def __init__(self, path: str, section_id: str):
        assert _match_input_path(path), f"Invalid path: '{path}'"
        self.path = path
        self.section_id = section_id
        object_name = self.object_name or "section"
        detail = f"{object_name.title()} '{section_id}' not found in '{path}'"
        super().__init__(HTTPStatus.NOT_FOUND, detail)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail


class ThermalClusterNotFound(ConfigSectionNotFound):
    """Thermal cluster is not found (404 Not Found)"""

    object_name = THERMAL_CLUSTER


class RenewableClusterNotFound(ConfigSectionNotFound):
    """Renewable cluster is not found (404 Not Found)"""

    object_name = RENEWABLE_CLUSTER


class STStorageNotFound(ConfigSectionNotFound):
    """Short-term storage is not found (404 Not Found)"""

    object_name = SHORT_TERM_STORAGE


class MatrixNotFound(HTTPException):
    """
    Exception raised when a matrix is not found (404 Not Found).

    Notes:
        The study ID is not provided because it is implicit.

    Attributes:
        path: Path of the missing file(s) relative to the study directory.
    """

    object_name = ""
    """Name of the object that is not found: thermal, renewables, etc."""

    def __init__(self, path: str):
        assert _match_input_path(path), f"Invalid path: '{path}'"
        self.path = path
        detail = f"Matrix '{path}' not found"
        if self.object_name:
            detail = f"{self.object_name.title()} {detail}"
        super().__init__(HTTPStatus.NOT_FOUND, detail)

    def __str__(self) -> str:
        return self.detail


class ThermalClusterMatrixNotFound(MatrixNotFound):
    """Matrix of the thermal cluster is not found (404 Not Found)"""

    object_name = THERMAL_CLUSTER


class RenewableClusterMatrixNotFound(MatrixNotFound):
    """Matrix of the renewable cluster is not found (404 Not Found)"""

    object_name = RENEWABLE_CLUSTER


class STStorageMatrixNotFound(MatrixNotFound):
    """Matrix of the short-term storage is not found (404 Not Found)"""

    object_name = SHORT_TERM_STORAGE


# ============================================================
# Duplicate (409)
# ============================================================


class DuplicateConfigSection(HTTPException):
    """
    Exception raised when a configuration section is duplicated (409 Conflict).

    Notes:
        The study ID is not provided because it is implicit.

    Attributes:
        area_id: ID of the area in which the section is duplicated.
        duplicates: Sequence of duplicated IDs.
    """

    object_name = ""
    """Name of the object that is duplicated: thermal, renewables, etc."""

    def __init__(self, area_id: str, *duplicates: str):
        self.area_id = area_id
        self.duplicates = duplicates
        ids = ", ".join(f"'{a}'" for a in duplicates)
        detail = {
            0: f"Duplicates found in '{area_id}'",
            1: f"Duplicate found in '{area_id}': {ids}",
            2: f"Duplicates found in '{area_id}': {ids}",
        }[min(len(duplicates), 2)]
        if self.object_name:
            detail = f"{self.object_name.title()} {detail}"
        super().__init__(HTTPStatus.CONFLICT, detail)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail


class DuplicateThermalCluster(DuplicateConfigSection):
    """Duplicate Thermal cluster (409 Conflict)"""

    object_name = THERMAL_CLUSTER


class DuplicateRenewableCluster(DuplicateConfigSection):
    """Duplicate Renewable cluster (409 Conflict)"""

    object_name = RENEWABLE_CLUSTER


class DuplicateSTStorage(DuplicateConfigSection):
    """Duplicate Short-term storage (409 Conflict)"""

    object_name = SHORT_TERM_STORAGE


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
    def __init__(self, uuid: str, message: t.Optional[str] = None) -> None:
        msg = f"Study {uuid} (not managed) is not allowed to be deleted"
        if message:
            msg += f"\n{message}"
        super().__init__(
            HTTPStatus.FORBIDDEN,
            msg,
        )


class StudyUpgradeRequirementsNotMet(HTTPException):
    def __init__(self, is_variant: bool, study_id: str) -> None:
        if is_variant:
            super().__init__(
                HTTPStatus.EXPECTATION_FAILED,
                f"Variant study {study_id} cannot be upgraded",
            )
        else:
            super().__init__(
                HTTPStatus.EXPECTATION_FAILED,
                f"Raw Study {study_id} cannot be upgraded: it has children studies",
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


class FileTooLargeError(HTTPException):
    def __init__(self, estimated_size: int, maximum_size: int) -> None:
        message = (
            f"Cannot aggregate output data."
            f" The expected size: {estimated_size}Mo exceeds the max supported size: {maximum_size}"
        )
        super().__init__(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, message)


class UrlNotMatchJsonDataError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class WritingInsideZippedFileException(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class BindingConstraintNotFound(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class NoConstraintError(HTTPException):
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


class MatrixWidthMismatchError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class WrongMatrixHeightError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class ConstraintTermNotFound(HTTPException):
    """
    Exception raised when a constraint term is not found.
    """

    def __init__(self, binding_constraint_id: str, *ids: str) -> None:
        count = len(ids)
        id_enum = ", ".join(f"'{term}'" for term in ids)
        message = {
            0: f"Constraint terms not found in BC '{binding_constraint_id}'",
            1: f"Constraint term {id_enum} not found in BC '{binding_constraint_id}'",
            2: f"Constraint terms {id_enum} not found in BC '{binding_constraint_id}'",
        }[min(count, 2)]
        super().__init__(HTTPStatus.NOT_FOUND, message)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail


class DuplicateConstraintTerm(HTTPException):
    """
    Exception raised when an attempt is made to create a constraint term which already exists.
    """

    def __init__(self, binding_constraint_id: str, *ids: str) -> None:
        count = len(ids)
        id_enum = ", ".join(f"'{term}'" for term in ids)
        message = {
            0: f"Constraint terms already exist in BC '{binding_constraint_id}'",
            1: f"Constraint term {id_enum} already exists in BC '{binding_constraint_id}'",
            2: f"Constraint terms {id_enum} already exist in BC '{binding_constraint_id}'",
        }[min(count, 2)]
        super().__init__(HTTPStatus.CONFLICT, message)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail


class InvalidConstraintTerm(HTTPException):
    """
    Exception raised when a constraint term is not correctly specified (no term data).
    """

    def __init__(self, binding_constraint_id: str, term_json: str) -> None:
        message = (
            f"Invalid constraint term for binding constraint '{binding_constraint_id}': {term_json},"
            f" term 'data' is missing or empty"
        )
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail


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
