import logging

from antarest.core.jwt import JWTUser
from antarest.core.model import PermissionInfo, StudyPermissionType, PublicMode
from antarest.core.roles import RoleType

logger = logging.getLogger(__name__)


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
    permission_info: PermissionInfo,
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
        permission_info: permission info to check
        permission: user permission to check

    Returns: true if user match permission requirements, false else.

    """
    if user.is_site_admin():
        return True

    if (
        permission_info.owner is not None
        and user.impersonator == permission_info.owner
    ):
        return True

    group_permission = any(
        role in permission_matrix[permission]["roles"]  # type: ignore
        for role in [
            group.role
            for group in (user.groups or [])
            if group.id in permission_info.groups
        ]
    )
    if group_permission:
        return True

    return permission_info.public_mode in permission_matrix[permission]["public_modes"]  # type: ignore
