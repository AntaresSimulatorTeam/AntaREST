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

from typing import List, Union

from antarest.core.roles import RoleType
from antarest.core.serde import AntaresBaseModel
from antarest.login.model import ADMIN_ID, Group, Identity


class JWTGroup(AntaresBaseModel):
    """
    Sub JWT domain with groups data belongs to user
    """

    id: str
    name: str
    role: RoleType


class JWTUser(AntaresBaseModel):
    """
    JWT domain with user data.
    """

    id: int
    type: str
    impersonator: int
    groups: List[JWTGroup] = []

    def is_admin_token(self) -> bool:
        """
        Returns: true if the user is a bot of admin

        """
        return self.impersonator == ADMIN_ID

    def is_site_admin(self) -> bool:
        """
        Returns: true if connected user is admin

        """
        return "admin" in [g.id for g in self.groups]

    def is_in_group(self, groups: Union[Group, List[Group]]) -> bool:
        """

        Args:
            groups: group or list of groups

        Returns: true if the user is in any of the groups given

        """
        if isinstance(groups, Group):
            return any(g.id == groups.id for g in self.groups)

        return any(self.is_in_group(g) for g in groups)

    def is_group_admin(self, groups: Union[Group, List[Group]]) -> bool:
        """

        Args:
            groups: group or list of groups

        Returns: true if user is admin of one of groups given

        """
        if isinstance(groups, Group):
            return any(g.id == groups.id and g.role == RoleType.ADMIN for g in self.groups)

        return any(self.is_group_admin(g) for g in groups)

    def is_himself(self, user: Identity) -> bool:
        """
        Compare user
        Args:
            user: user to compare

        Returns: true if user are identical

        """
        return bool(self.id == user.id)

    def is_bot_of(self, user: Identity) -> bool:
        """
        Check if the current identity if a bot from a given user
        Args:
            user: the user to check if it's been impersonated by the bot

        Returns: true if the user is impersonnated by the current identity
        """
        return bool(self.impersonator == user.id)

    def is_or_impersonate(self, user_id: int) -> bool:
        """
        Check if the current identity if a bot of or the user itself
        Args:
            user_id: the user id to check if it's been impersonated or himself

        Returns: true if the user is (or impersonnated) by the current identity
        """
        return self.id == user_id or self.impersonator == user_id


DEFAULT_ADMIN_USER = JWTUser(
    id=ADMIN_ID,
    impersonator=ADMIN_ID,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)
