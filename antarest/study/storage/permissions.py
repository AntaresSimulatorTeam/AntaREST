import enum
import logging
from typing import Optional, Union

from antarest.core.jwt import JWTUser
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.roles import RoleType
from antarest.study.model import PublicMode, Study, StudyMetadataDTO

logger = logging.getLogger(__name__)


class StudyPermissionType(enum.Enum):
    """
    User permission belongs to Study
    """

    READ = "READ"
    RUN = "RUN"
    WRITE = "WRITE"
    DELETE = "DELETE"
    MANAGE_PERMISSIONS = "MANAGE_PERMISSIONS"


permission_matrix = {
    StudyPermissionType.READ: {
        "roles": [
            RoleType.ADMIN,
            RoleType.RUNNER,
            RoleType.WRITER,
            RoleType.READER,
        ],
        "public_modes": [
            PublicMode.FULL,
            PublicMode.EDIT,
            PublicMode.EXECUTE,
            PublicMode.READ,
        ],
    },
    StudyPermissionType.RUN: {
        "roles": [RoleType.ADMIN, RoleType.RUNNER, RoleType.WRITER],
        "public_modes": [PublicMode.FULL, PublicMode.EDIT, PublicMode.EXECUTE],
    },
    StudyPermissionType.WRITE: {
        "roles": [RoleType.ADMIN, RoleType.WRITER],
        "public_modes": [PublicMode.FULL, PublicMode.EDIT],
    },
    StudyPermissionType.DELETE: {
        "roles": [RoleType.ADMIN],
        "public_modes": [PublicMode.FULL],
    },
    StudyPermissionType.MANAGE_PERMISSIONS: {
        "roles": [RoleType.ADMIN],
        "public_modes": [],
    },
}


def check_permission(
    user: JWTUser,
    study: Union[Study, StudyMetadataDTO],
    permission: StudyPermissionType,
) -> bool:
    """
    Check user permission on study. User has permission if
    - user is site admin
    - user is the study owner
    - user has correct role of one group linked to study
    - study is public

    Args:
        user: user logged
        study: study to check
        permission: user permission to check

    Returns: true if user match permission requirements, false else.

    """
    if user.is_site_admin():
        logger.debug(f"user {user.id} accepted on study {study.id} as admin")
        return True

    if study.owner is not None and user.impersonator == study.owner.id:
        logger.debug(f"user {user.id} accepted on study {study.id} as owner")
        return True

    study_group_id = [g.id for g in study.groups if g.id is not None]
    group_permission = any(
        role in permission_matrix[permission]["roles"]  # type: ignore
        for role in [
            group.role
            for group in (user.groups or [])
            if group.id in study_group_id
        ]
    )
    if group_permission:
        logger.debug(
            f"user {user.id} accepted on study {study.id} as admin of at least one group"
        )
        return True

    return study.public_mode in permission_matrix[permission]["public_modes"]  # type: ignore


def assert_permission(
    user: Optional[JWTUser],
    study: Optional[Union[Study, StudyMetadataDTO]],
    permission_type: StudyPermissionType,
    raising: bool = True,
) -> bool:
    """
    Assert user has permission to edit or read study.
    Args:
        user: user logged
        study: study asked
        permission_type: level of permission
        raising: raise error if permission not matched

    Returns: true if permission match, false if not raising.

    """
    if not user:
        logger.error("FAIL permission: user is not logged")
        raise UserHasNotPermissionError()

    if not study:
        logger.error("FAIL permission: study not exist")
        raise ValueError("Metadata is None")

    ok = check_permission(user, study, permission_type)
    if raising and not ok:
        logger.error(
            "FAIL permission: user %d has no permission on study %s",
            user.id,
            study.id,
        )
        raise UserHasNotPermissionError()

    return ok
