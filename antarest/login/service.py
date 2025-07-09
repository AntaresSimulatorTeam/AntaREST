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

import logging
from typing import List, Optional, Union, cast

from fastapi import HTTPException

from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.roles import RoleType
from antarest.login.ldap import LdapService
from antarest.login.model import (
    Bot,
    BotCreateDTO,
    BotIdentityDTO,
    Group,
    GroupDetailDTO,
    GroupDTO,
    Identity,
    IdentityDTO,
    Password,
    Role,
    RoleCreationDTO,
    RoleDTO,
    User,
    UserCreateDTO,
    UserInfo,
    UserLdap,
    UserRoleDTO,
)
from antarest.login.repository import BotRepository, GroupRepository, IdentityRepository, RoleRepository, UserRepository
from antarest.login.utils import get_current_user, get_user_id

logger = logging.getLogger(__name__)


class GroupNotFoundError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail="Group not found")


class UserNotFoundError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail="User not found")


class LoginService:
    """
    Facade module service to handle request to manage user, group and role
    """

    def __init__(
        self,
        user_repo: UserRepository,
        identity_repo: IdentityRepository,
        bot_repo: BotRepository,
        group_repo: GroupRepository,
        role_repo: RoleRepository,
        ldap: LdapService,
        event_bus: IEventBus,
    ):
        self.users = user_repo
        self.identities = identity_repo
        self.bots = bot_repo
        self.groups = group_repo
        self.roles = role_repo
        self.ldap = ldap
        self.event_bus = event_bus

    def save_group(self, group: Group) -> Group:
        """
        Create / Update group.
        Permission: SADMIN, GADMIN (own group)
        Args:
            group: group to stored

        Returns: group

        """
        if self.groups.get_by_name(cast(str, group.name)):
            raise HTTPException(status_code=400, detail="Group name already exists")

        user = get_current_user()
        if user and any((user.is_site_admin(), user.is_group_admin(group))):
            logger.info(
                "%s (%s) saved by user %s",
                group.name,
                group.id,
                get_user_id(),
            )
            return self.groups.save(group)
        else:
            logger.error("user %s has not permission to save group", get_user_id())
            raise UserHasNotPermissionError()

    def create_user(self, create: UserCreateDTO) -> Identity:
        """
        Create new user.
        Permission: SADMIN
        Args:
            create: user to create
        Returns: user stored

        """
        user = get_current_user()
        if user and user.is_site_admin():
            if self.users.get_by_name(create.name):
                logger.error("user %s already exist", create.name)
                raise HTTPException(status_code=400, detail="User already exists")
            return self.users.save(User(name=create.name, password=Password(create.password)))
        else:
            logger.error("User %s has no permission to create user", get_user_id())
            raise UserHasNotPermissionError()

    def save_user(self, user: User) -> User:
        """
        Update user data
        Permission: SADMIN, USER (own user)
        Args:
            user: new user

        Returns: new user

        """
        current_user = get_current_user()
        if current_user and any((current_user.is_site_admin(), current_user.is_himself(user))):
            logger.info("user %d saved by user %s", user.id, get_user_id())
            return self.users.save(user)
        else:
            logger.error("user %s has not permission to save user %d", get_user_id(), user.id)
            raise UserHasNotPermissionError()

    def save_bot(self, bot: BotCreateDTO) -> Bot:
        """
        Create bot
        Permission: User (own user)
        Args:
            bot: bot to create

        Returns: bot created

        """
        user = get_current_user()
        if user:
            if not user.is_site_admin():
                for role_create in bot.roles:
                    role = self.roles.get(user.id, role_create.group)
                    if not role or role.type is None or role.type < role_create.role:
                        raise UserHasNotPermissionError()

            if not bot.name.strip():
                raise HTTPException(status_code=400, detail="Bot name must not be empty")

            if self.bots.get_by_name_and_owner(owner=user.id, name=bot.name):
                raise HTTPException(status_code=400, detail="Bot name already exists")

            b = self.bots.save(
                Bot(
                    name=bot.name,
                    is_author=bot.is_author,
                    owner=user.id,
                )
            )

            for role_create in bot.roles:
                role_type = RoleType(role_create.role)
                self.roles.save(
                    Role(
                        group=Group(id=role_create.group),
                        type=role_type,
                        identity=b,
                    )
                )
            logger.info(
                "bot %s (%d) created by user %s",
                bot.name,
                b.id,
                get_user_id(),
            )
            return b
        else:
            logger.error(
                "user %s has not permission to create bot",
                get_user_id(),
            )
            raise UserHasNotPermissionError()

    def save_role(self, role: RoleCreationDTO) -> Role:
        """
        Create / Update role
        Permission: SADMIN, GADMIN (own group)
        Args:
            role: new role

        Returns: role stored

        """
        role_obj = Role(
            type=role.type,
            group=self.groups.get(role.group_id),
            identity=self.users.get(role.identity_id) or self.ldap.get(role.identity_id),
        )
        user = get_current_user()
        if user and any(
            (
                user.is_site_admin(),
                user.is_group_admin(role_obj.group),
            )
        ):
            logger.info(
                "role (user=%s, group=%s) created by user %s",
                role.identity_id,
                role.group_id,
                get_user_id(),
            )
            return self.roles.save(role_obj)
        else:
            logger.error(
                "user %s, has not permission to create role (user=%d, group=%s)",
                get_user_id(),
                role.identity_id,
                role.group_id,
            )
            raise UserHasNotPermissionError()

    def get_group(self, id: str) -> Optional[Group]:
        """
        Get group.
        Permission: SADMIN, all users that belong to the group

        Args:
            id: group id

        Returns: group asked

        """
        user = get_current_user()
        if user is None:
            user_id = get_user_id()
            err_msg = f"user {user_id} has not permission to get group"
            logger.error(err_msg)
            raise UserHasNotPermissionError(err_msg)

        group = self.groups.get(id)
        if group is not None and any(
            (
                user.is_site_admin(),
                id in [group.id for group in user.groups],
            )
        ):
            return group
        else:
            logger.error("group %s not found by user %s", id, get_user_id())
            raise GroupNotFoundError()

    def get_group_info(self, id: str) -> Optional[GroupDetailDTO]:
        """
        Get group.
        Permission: SADMIN, GADMIN (own group)

        Args:
            id: group id

        Returns: group and list of users

        """
        group = self.get_group(id)
        if group:
            user_list = []
            roles = self.get_all_roles_in_group(group.id)
            for role in roles:
                user = self.get_identity(role.identity_id)
                if user:
                    user_list.append(UserRoleDTO(id=user.id, name=user.name, role=role.type))
            return GroupDetailDTO(id=group.id, name=group.name, users=user_list)
        else:
            logger.error("group %s not found by user %s", id, get_user_id())
            raise GroupNotFoundError()

    def get_user(self, id: int) -> Optional[User]:
        """
        Get user
        Permission: SADMIN, GADMIN (own group), USER (own user)

        Args:
            id: user id

        Returns: user

        """
        user = self.ldap.get(id) or self.users.get(id)
        if not user:
            logger.error("user %d not found by user %s", id, get_user_id())
            raise UserNotFoundError()

        groups = [r.group for r in self.roles.get_all_by_user(user.id)]

        current_user = get_current_user()
        if current_user and any(
            (
                current_user.is_site_admin(),
                current_user.is_in_group(groups),
                current_user.is_himself(user),
                current_user.is_bot_of(user),
            )
        ):
            return user
        else:
            logger.error(
                "user %d info not allowed to fetch by user %s",
                id,
                get_user_id(),
            )
            return None

    def get_identity(self, id: int, include_token: bool = False) -> Optional[Identity]:
        """
        Get user, LDAP user or bot.

        Args:
            id: ID of the user to fetch
            include_token: whether to include the bots or not.

        Returns:
            The user, LDAP user or bot if found, `None` otherwise.
        """
        user = self.ldap.get(id) or self.users.get(id)
        if include_token:
            return user or self.bots.get(id)
        return user

    def get_user_info(self, id: int) -> Optional[IdentityDTO]:
        """
        Get user information
        Permission: SADMIN, GADMIN (own group), USER (own user)

        Args:
            id: user id

        Returns: user information and roles

        """
        user = self.get_user(id)
        if user:
            return IdentityDTO(
                id=user.id,
                name=user.name,
                roles=[
                    RoleDTO(
                        group_id=role.group_id,
                        group_name=role.group.name,
                        identity_id=id,
                        type=role.type.value,
                    )
                    for role in self.roles.get_all_by_user(user.id)
                ],
            )
        return None

    def get_bot(self, id: int) -> Bot:
        """
        Get bot.
        Permission: SADMIN, USER (owner)

        Args:
            id: bot id
        Returns: bot

        """
        user = get_current_user()
        bot = self.bots.get(id)
        if (
            bot
            and user
            and any(
                (
                    user.is_site_admin(),
                    user.is_himself(user=Identity(id=bot.owner)),
                )
            )
        ):
            return bot
        else:
            logger.error("bot %d not found by user %s", id, get_user_id())
            raise UserHasNotPermissionError()

    def get_bot_info(self, id: int) -> Optional[BotIdentityDTO]:
        """
        Get user information
        Permission: SADMIN, GADMIN (own group), USER (own user)

        Args:
            id: bot id

        Returns: bot information and roles

        """
        bot = self.get_bot(id)
        return BotIdentityDTO(
            id=bot.id,
            name=bot.name,
            isAuthor=bot.is_author,
            roles=[
                RoleDTO(
                    group_id=role.group_id,
                    group_name=role.group.name,
                    identity_id=id,
                    type=role.type.value,
                )
                for role in self.roles.get_all_by_user(bot.id)
            ],
        )

    def get_all_bots_by_owner(self, owner: int) -> List[Bot]:
        """
        Get by bo owned by a user
        Permission: SADMIN, USER (owner)

        Args:
            owner: bots owner id

        Returns: list of bot owned by user

        """
        user = get_current_user()
        if user and any(
            (
                user.is_site_admin(),
                user.is_himself(Identity(id=owner)),
            )
        ):
            return self.bots.get_all_by_owner(owner)
        else:
            logger.error(
                "user %s has not permission to fetch bots owner=%d",
                get_user_id(),
                owner,
            )
            raise UserHasNotPermissionError()

    def exists_bot(self, id: int) -> bool:
        """
        Check if bot exist.

        Args:
            id: bot id

        Returns: true if bot exist, false else.

        """
        return self.bots.exists(id)

    def authenticate(self, name: str, pwd: str) -> Optional[JWTUser]:
        """
        Check if password match username stored in DB.
        Args:
            name: username
            pwd: user password

        Returns: jwt data with user information if auth success, None else.

        """
        intern: Optional[User] = self.users.get_by_name(name)
        if intern and intern.password.check(pwd):
            logger.info("successful login from intern user %s", name)
            return self.get_jwt(intern.id)

        extern = self.ldap.login(name, pwd)
        if extern:
            logger.info("successful login from ldap user %s", name)
            return self.get_jwt(extern.id)

        logger.error("wrong authentication from user %s", name)
        return None

    def get_jwt(self, user_id: int) -> Optional[JWTUser]:
        """
        Build a jwt data from user id.

        Args:
            user_id: user id

        Returns: jwt data with user information.

        """
        user = self.ldap.get(user_id) or self.users.get(user_id)
        if user:
            logger.info("JWT claimed for user=%d", user_id)
            return JWTUser(
                id=user.id,
                impersonator=user.get_impersonator(),
                type=user.type,
                groups=[
                    JWTGroup(id=r.group.id, name=r.group.name, role=r.type) for r in self.roles.get_all_by_user(user_id)
                ],
            )

        logger.error("Can't claim JWT for user=%d", user_id)
        return None

    def get_all_groups(self, details: bool = False) -> List[Union[GroupDetailDTO, GroupDTO]]:
        """
        Get all groups.
        Permission: SADMIN
        Args:
            details: If False, only get group name and id.
            If True, for each group, fetch every user in the group with their role

        Returns: list of groups

        """
        user = get_current_user()
        if not user:
            logger.error(
                "user %s has not permission to get all groups",
                get_user_id(),
            )
            raise UserHasNotPermissionError()

        # No details needed
        if not details:
            if user.is_site_admin():
                group_list = self.groups.get_all()
            else:
                group_list = [r.group for r in self.roles.get_all_by_user(user.id)]
            return [group.to_dto() for group in group_list]

        # User details needed
        users_by_group: dict[tuple[str, str], List[UserRoleDTO]] = {}
        all_users = self.get_all_users(details=True)
        for identity in all_users:
            assert isinstance(identity, IdentityDTO)
            for role in identity.roles:
                group_id, group_name = role.group_id, role.group_name
                assert group_id is not None
                users_by_group.setdefault((group_id, group_name), []).append(
                    UserRoleDTO(id=identity.id, name=identity.name, role=role.type)
                )

        return [GroupDetailDTO(id=key[0], name=key[1], users=users) for key, users in users_by_group.items()]

    def _get_user_by_group(self, group: str) -> List[Identity]:
        roles = self.roles.get_all_by_group(group)
        user_list = []
        for role in roles:
            user = self.get_identity(role.identity_id)
            if user:
                user_list.append(user)
        return user_list

    def get_all_users(self, details: bool = False) -> List[Union[UserInfo, IdentityDTO]]:
        """
        Get all users.
        Permission: SADMIN
        Args:
            details: If False, only get user's name and id.
            If True, for each user, fetch all his groups and his role inside it

        Returns: list of groups

        """
        user = get_current_user()

        if not user:
            logger.error(
                "user %s has not permission to get all users",
                get_user_id(),
            )
            raise UserHasNotPermissionError()

        # Get all users
        # WARNING: This list contains all users, so we should filter it afterward to avoid accessing info we shouldn't
        all_users = self.identities.get_all_users()

        # Easy case: we don't need more information
        if user.is_site_admin() and not details:
            return [user.to_dto() for user in all_users]

        # Get roles
        if user.is_site_admin():
            groups = None
        else:
            groups = [r.group for r in self.roles.get_all_by_user(user.id)]
            if not groups:
                # The user has no groups, he can only fetch himself
                user_id = user.id
                user_name = next(iter(identity.name for identity in all_users if identity.id == user_id))
                if details:
                    return [IdentityDTO(id=user_id, name=user_name, roles=[])]
                return [UserInfo(id=user_id, name=user_name)]

        all_roles = self.roles.get_all(details=details, groups=groups)

        # Builds a map from a user to all his roles
        roles_per_user: dict[int, List[RoleDTO]] = {}
        for role in all_roles:
            roles_per_user.setdefault(role.identity_id, []).append(
                RoleDTO(
                    group_id=role.group_id,
                    group_name=role.group.name,
                    identity_id=role.identity_id,
                    type=role.type,
                )
            )

        # For the admin, loop through every user and build the return containing role information
        if user.is_site_admin():
            return [
                IdentityDTO(id=identity.id, name=identity.name, roles=roles_per_user.get(identity.id, []))
                for identity in all_users
            ]

        # For other users, we need to loop on the map we built earlier to avoid accessing info the user shouldn't have
        user_mapping_id_to_name = {user.id: user.name for user in all_users}
        if details:
            return [
                IdentityDTO(
                    id=id,
                    name=user_mapping_id_to_name[id],
                    roles=roles_per_user[id],
                )
                for id in roles_per_user
            ]
        return [UserInfo(id=id, name=user_mapping_id_to_name[id]) for id in roles_per_user]

    def get_all_bots(self) -> List[Bot]:
        """
        Get all bots
        Permission: SADMIN
        """
        user = get_current_user()
        if user and user.is_site_admin():
            return self.bots.get_all()
        else:
            logger.error(
                "user %s has not permission to get all bots",
                get_user_id(),
            )
            raise UserHasNotPermissionError()

    def get_all_roles_in_group(self, group: str) -> List[Role]:
        """
        Get all roles inside a group
        Permission: SADMIN, GADMIN (own group)

        Args:
            group: group linked to role

        Returns: list of role

        """
        user = get_current_user()
        if user and any(
            (
                user.is_site_admin(),
                user.is_group_admin(Group(id=group)),
            )
        ):
            return self.roles.get_all_by_group(group)
        else:
            logger.error(
                "user %s has not permission to get all roles in group %s",
                get_user_id(),
                group,
            )
            raise UserHasNotPermissionError()

    def delete_group(self, id: str) -> None:
        """
        Delete group
        Permission: SADMIN, GADMIN (own group)
        Args:
            id: group id to delete

        Returns:

        """
        user = get_current_user()
        if user and any(
            (
                user.is_site_admin(),
                user.is_group_admin(Group(id=id)),
            )
        ):
            for role in self.roles.get_all_by_group(group=id):
                self.roles.delete(user=role.identity_id, group=role.group_id)

            logger.info("group %s deleted by user %s", id, get_user_id())
            return self.groups.delete(id)
        else:
            logger.error(
                "user %s has not permission to delete group %s",
                get_user_id(),
                id,
            )
            raise UserHasNotPermissionError()

    def delete_user(self, id: int) -> None:
        """
        Delete user
        Permission: SADMIN, USER (own user)
        Args:
            id: user id

        Returns:

        """
        user = get_current_user()
        if user and any((user.is_site_admin(), user.is_himself(User(id=id)))):
            for b in self.bots.get_all_by_owner(id):
                self.delete_bot(b.id)

            self.delete_all_roles_from_user(id)

            logger.info("user %s deleted by user %s", id, get_user_id())

            user = self.get_user(id)
            if isinstance(user, UserLdap):
                return self.ldap.delete(id)
            else:
                return self.users.delete(id)  # return for test purpose

        else:
            logger.info(
                "user %s has not permission to delete user %d",
                get_user_id(),
                id,
            )
            raise UserHasNotPermissionError()

    def delete_bot(self, id: int) -> None:
        """
        Delete bot
        Permission: SADMIN, USER (owner)
        Args:
            id: bot id

        Returns:

        """
        user = get_current_user()
        bot = self.bots.get(id)
        if (
            user
            and bot
            and any(
                (
                    user.is_site_admin(),
                    user.is_himself(Identity(id=bot.owner)),
                )
            )
        ):
            logger.info("bot %d deleted by user %s", id, get_user_id())
            for role in self.roles.get_all_by_user(id):
                self.roles.delete(user=role.identity_id, group=role.group_id)
            return self.bots.delete(id)
        else:
            logger.error(
                "user %s has not permission to delete bot %d",
                get_user_id(),
                id,
            )
            raise UserHasNotPermissionError()

    def delete_role(self, user: int, group: str) -> None:
        """
        Delete role
        Permission: SADMIN, GADMIN (own group)
        Args:
            user: user linked to role
            group: group linked to role

        Returns:

        """
        current_user = get_current_user()
        if current_user and any(
            (
                current_user.is_site_admin(),
                current_user.is_group_admin(Group(id=group)),
            )
        ):
            logger.info(
                "role (user=%d, group=%s) deleted by %s",
                user,
                group,
                get_user_id(),
            )
            return self.roles.delete(user, group)
        else:
            logger.error(
                "user %s has not permission to delete role (user=%d, group=%s)",
                get_user_id(),
                user,
                group,
            )
            raise UserHasNotPermissionError()

    def delete_all_roles_from_user(self, id: int) -> int:
        """
        Delete all roles from a specific user
        Permission: SADMIN, GADMIN (own group)
        Args:
            id: user linked to roles

        Returns:

        """
        roles = self.roles.get_all_by_user(id)
        groups = [r.group for r in roles]
        user = get_current_user()
        if user and any(
            (
                user.is_site_admin(),
                user.is_group_admin(groups),
            )
        ):
            for role in roles:
                self.roles.delete(role.identity_id, role.group_id)
            return id
        else:
            raise UserHasNotPermissionError()
