import enum

from antarest.common.jwt import JWTUser
from antarest.common.roles import RoleType
from antarest.storage.model import PublicMode, Study


class StudyPermissionType(enum.Enum):
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
    user: JWTUser, study: Study, permission: StudyPermissionType
):
    if user.is_site_admin():
        return True

    if study.owner is not None and user.id == study.owner.id:
        return True

    global permission_matrix
    study_group_id = [g.id for g in study.groups]
    group_permission = any(
        role in permission_matrix[permission]["roles"]
        for role in [
            group.role
            for group in (user.groups or [])
            if group.id in study_group_id
        ]
    )
    if group_permission:
        return True

    return study.public_mode in permission_matrix[permission]["public_modes"]
