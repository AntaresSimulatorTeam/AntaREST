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

import re
from http import HTTPStatus
from typing import Optional, Sequence

from fastapi.exceptions import HTTPException
from typing_extensions import override


class ShouldNotHappenException(Exception):
    pass


class MustNotModifyOutputException(Exception):
    def __init__(self, file_name: str) -> None:
        msg = f"Should not modify output file {file_name}"
        super().__init__(msg)


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

    @override
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

    @override
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

    @override
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

    @override
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


class LinkValidationError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class LinkNotFound(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


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


class StudyVariantUpgradeError(HTTPException):
    def __init__(self, is_variant: bool) -> None:
        if is_variant:
            super().__init__(
                HTTPStatus.EXPECTATION_FAILED,
                "Upgrade not supported for variant study",
            )
        else:
            super().__init__(HTTPStatus.EXPECTATION_FAILED, "Upgrade not supported for parent of variants")


class ResourceDeletionNotAllowed(HTTPException):
    """
    Exception raised when deleting a file or a folder which isn't inside the 'User' folder.
    """

    def __init__(self, message: str) -> None:
        msg = f"Resource deletion failed because {message}"
        super().__init__(HTTPStatus.FORBIDDEN, msg)


class FolderCreationNotAllowed(HTTPException):
    """
    Exception raised when creating a folder which isn't inside the 'User' folder.
    """

    def __init__(self, message: str) -> None:
        msg = f"Folder creation failed because {message}"
        super().__init__(HTTPStatus.FORBIDDEN, msg)


class ReferencedObjectDeletionNotAllowed(HTTPException):
    """
    Exception raised when a binding constraint is not allowed to be deleted because it references
    other objects: areas, links or thermal clusters.
    """

    def __init__(self, object_id: str, binding_ids: Sequence[str], *, object_type: str) -> None:
        """
        Initialize the exception.

        Args:
            object_id: ID of the object that is not allowed to be deleted.
            binding_ids: Binding constraints IDs that reference the object.
            object_type: Type of the object that is not allowed to be deleted: area, link or thermal cluster.
        """
        max_count = 10
        first_bcs_ids = ",\n".join(f"{i}- '{bc}'" for i, bc in enumerate(binding_ids[:max_count], 1))
        and_more = f",\nand {len(binding_ids) - max_count} more..." if len(binding_ids) > max_count else "."
        message = (
            f"{object_type} '{object_id}' is not allowed to be deleted, because it is referenced"
            f" in the following binding constraints:\n{first_bcs_ids}{and_more}"
        )
        super().__init__(HTTPStatus.FORBIDDEN, message)

    @override
    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail


class UnsupportedStudyVersion(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class UnsupportedOperationOnArchivedStudy(HTTPException):
    def __init__(self, uuid: str) -> None:
        super().__init__(
            HTTPStatus.BAD_REQUEST,
            f"Study {uuid} is archived",
        )


class BadOutputError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class OutputNotFound(HTTPException):
    """
    Exception raised when an output is not found in the study results directory.
    """

    def __init__(self, output_id: str) -> None:
        message = f"Output '{output_id}' not found"
        super().__init__(HTTPStatus.NOT_FOUND, message)

    @override
    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail


class OutputAlreadyArchived(HTTPException):
    """
    Exception raised when a user wants to archive an output which is already archived.
    """

    def __init__(self, output_id: str) -> None:
        message = f"Output '{output_id}' is already archived"
        super().__init__(HTTPStatus.EXPECTATION_FAILED, message)


class OutputAlreadyUnarchived(HTTPException):
    """
    Exception raised when a user wants to unarchive an output which is already unarchived.
    """

    def __init__(self, output_id: str) -> None:
        message = f"Output '{output_id}' is already unarchived"
        super().__init__(HTTPStatus.EXPECTATION_FAILED, message)


class OutputSubFolderNotFound(HTTPException):
    """
    Exception raised when an output sub folders do not exist
    """

    def __init__(self, output_id: str, mc_root: str) -> None:
        message = f"The output '{output_id}' sub-folder '{mc_root}' does not exist"
        super().__init__(HTTPStatus.NOT_FOUND, message)

    @override
    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail


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


class MCRootNotHandled(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class MatrixWidthMismatchError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class WrongMatrixHeightError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class MatrixImportFailed(HTTPException):
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

    @override
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

    @override
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

    @override
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


class CannotAccessInternalWorkspace(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            HTTPStatus.BAD_REQUEST,
            "You cannot scan the default internal workspace",
        )


class ChildNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class PathIsAFolderError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class WorkspaceNotFound(HTTPException):
    """
    This will be raised when we try to load a workspace that does not exist
    """

    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class BadArchiveContent(Exception):
    """
    Exception raised when the archive file is corrupted (or unknown).
    """

    def __init__(self, message: str = "Unsupported archive format") -> None:
        super().__init__(message)


class FolderNotFoundInWorkspace(HTTPException):
    """
    This will be raised when we try to load a folder that does not exist
    """

    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class XpansionConfigurationAlreadyExists(Exception):
    def __init__(self, study_id: str) -> None:
        super().__init__(HTTPStatus.CONFLICT, f"Xpansion configuration already exists for study {study_id}")


class XpansionFileAlreadyExistsError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.CONFLICT, message)


class FileCurrentlyUsedInSettings(HTTPException):
    def __init__(self, resource_type: str, filename: str) -> None:
        msg = f"The {resource_type} file '{filename}' is still used in the xpansion settings and cannot be deleted"
        super().__init__(HTTPStatus.CONFLICT, msg)
