# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import logging

from antarest.core.jwt import JWTUser
from antarest.core.model import PermissionInfo, PublicMode, StudyPermissionType
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
    if user.is_site_admin() or user.is_admin_token():
        return True

    if permission_info.owner is not None and user.impersonator == permission_info.owner:
        return True

    allowed_roles = permission_matrix[permission]["roles"]
    group_permission = any(
        role in allowed_roles  # type: ignore
        for role in [group.role for group in (user.groups or []) if group.id in permission_info.groups]
    )
    if group_permission:
        return True

    allowed_public_modes = permission_matrix[permission]["public_modes"]
    return permission_info.public_mode in allowed_public_modes  # type: ignore
