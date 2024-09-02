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
from typing import List, Optional, Union

from fastapi import HTTPException

from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
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
from antarest.login.repository import BotRepository, GroupRepository, RoleRepository, UserRepository

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
        bot_repo: BotRepository,
        group_repo: GroupRepository,
        role_repo: RoleRepository,
        ldap: LdapService,
        event_bus: IEventBus,
    ):
        self.users = user_repo
        self.bots = bot_repo
        self.groups = group_repo
        self.roles = role_repo
        self.ldap = ldap
        self.event_bus = event_bus

    def save_group(self, group: Group, params: RequestParameters) -> Group:
        """
        Create / Update group.
        Permission: SADMIN, GADMIN (own group)
        Args:
            group: group to stored
            params: request parameters

        Returns: group

        """
        if self.groups.get_by_name(group.name):
            raise HTTPException(status_code=400, detail="Group name already exists")

        if params.user and any((params.user.is_site_admin(), params.user.is_group_admin(group))):
            logger.info(
                "%s (%s) saved by user %s",
                group.name,
                group.id,
                params.get_user_id(),
            )
            return self.groups.save(group)
        else:
            logger.error(
                "user %s has not permission to save group",
                params.get_user_id(),
            )
            raise UserHasNotPermissionError()

    def create_user(self, create: UserCreateDTO, param: RequestParameters) -> Identity:
        """
        Create new user.
        Permission: SADMIN
        Args:
            create: user to create
            param: request parameters

        Returns: user stored

        """
        if param.user and param.user.is_site_admin():
            if self.users.get_by_name(create.name):
                logger.error("user %s already exist", create.name)
                raise HTTPException(status_code=400, detail="User already exists")
            return self.users.save(User(name=create.name, password=Password(create.password)))
        else:
            logger.error("User %s has no permission to create user", param.get_user_id())
            raise UserHasNotPermissionError()

    def save_user(self, user: User, params: RequestParameters) -> User:
        """
        Update user data
        Permission: SADMIN, USER (own user)
        Args:
            user: new user
            params: requests parameters

        Returns: new user

        """
        if params.user and any((params.user.is_site_admin(), params.user.is_himself(user))):
            logger.info("user %d saved by user %s", user.id, params.get_user_id())
            return self.users.save(user)
        else:
            logger.error(
                "user %s has not permission to save user %d",
                params.get_user_id(),
                user.id,
            )
            raise UserHasNotPermissionError()

    def save_bot(self, bot: BotCreateDTO, params: RequestParameters) -> Bot:
        """
        Create bot
        Permission: User (own user)
        Args:
            bot: bot to create
            params: request parameters

        Returns: bot created

        """

        if params.user:
            if not params.user.is_site_admin():
                for role_create in bot.roles:
                    role = self.roles.get(params.user.id, role_create.group)
                    if not role or role.type is None or role.type < role_create.role:
                        raise UserHasNotPermissionError()

            if not bot.name.strip():
                raise HTTPException(status_code=400, detail="Bot name must not be empty")

            if self.bots.get_by_name_and_owner(owner=params.user.id, name=bot.name):
                raise HTTPException(status_code=400, detail="Bot name already exists")

            b = self.bots.save(
                Bot(
                    name=bot.name,
                    is_author=bot.is_author,
                    owner=params.user.id,
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
                params.get_user_id(),
            )
            return b
        else:
            logger.error(
                "user %s has not permission to create bot",
                params.get_user_id(),
            )
            raise UserHasNotPermissionError()

    def save_role(self, role: RoleCreationDTO, params: RequestParameters) -> Role:
        """
        Create / Update role
        Permission: SADMIN, GADMIN (own group)
        Args:
            role: new role
            params: request parameters

        Returns: role stored

        """
        role_obj = Role(
            type=role.type,
            group=self.groups.get(role.group_id),
            identity=self.users.get(role.identity_id) or self.ldap.get(role.identity_id),
        )
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(role_obj.group),
            )
        ):
            logger.info(
                "role (user=%s, group=%s) created by user %s",
                role.identity_id,
                role.group_id,
                params.get_user_id(),
            )
            return self.roles.save(role_obj)
        else:
            logger.error(
                "user %s, has not permission to create role (user=%d, group=%s)",
                params.get_user_id(),
                role.identity_id,
                role.group_id,
            )
            raise UserHasNotPermissionError()

    def get_group(self, id: str, params: RequestParameters) -> Optional[Group]:
        """
        Get group.
        Permission: SADMIN, all users that belong to the group

        Args:
            id: group id
            params: request parameters

        Returns: group asked

        """
        if params.user is None:
            user_id = params.get_user_id()
            err_msg = f"user {user_id} has not permission to get group"
            logger.error(err_msg)
            raise UserHasNotPermissionError(err_msg)

        group = self.groups.get(id)
        if group is not None and any(
            (
                params.user.is_site_admin(),
                id in [group.id for group in params.user.groups],
            )
        ):
            return group
        else:
            logger.error("group %s not found by user %s", id, params.get_user_id())
            raise GroupNotFoundError()

    def get_group_info(self, id: str, params: RequestParameters) -> Optional[GroupDetailDTO]:
        """
        Get group.
        Permission: SADMIN, GADMIN (own group)

        Args:
            id: group id
            params: request parameters

        Returns: group and list of users

        """
        group = self.get_group(id, params)
        if group:
            user_list = []
            roles = self.get_all_roles_in_group(group.id, params)
            for role in roles:
                user = self.get_identity(role.identity_id)
                if user:
                    user_list.append(UserRoleDTO(id=user.id, name=user.name, role=role.type))
            return GroupDetailDTO(id=group.id, name=group.name, users=user_list)
        else:
            logger.error("group %s not found by user %s", id, params.get_user_id())
            raise GroupNotFoundError()

    def get_user(self, id: int, params: RequestParameters) -> Optional[User]:
        """
        Get user
        Permission: SADMIN, GADMIN (own group), USER (own user)

        Args:
            id: user id
            params: request parameters

        Returns: user

        """
        user = self.ldap.get(id) or self.users.get(id)
        if not user:
            logger.error("user %d not found by user %s", id, params.get_user_id())
            raise UserNotFoundError()

        groups = [r.group for r in self.roles.get_all_by_user(user.id)]

        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_in_group(groups),
                params.user.is_himself(user),
                params.user.is_bot_of(user),
            )
        ):
            return user
        else:
            logger.error(
                "user %d info not allowed to fetch by user %s",
                id,
                params.get_user_id(),
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

    def get_user_info(self, id: int, params: RequestParameters) -> Optional[IdentityDTO]:
        """
        Get user information
        Permission: SADMIN, GADMIN (own group), USER (own user)

        Args:
            id: user id
            params: request parameters

        Returns: user information and roles

        """
        user = self.get_user(id, params)
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

    def get_bot(self, id: int, params: RequestParameters) -> Bot:
        """
        Get bot.
        Permission: SADMIN, USER (owner)

        Args:
            id: bot id
            params: request parameters

        Returns: bot

        """
        bot = self.bots.get(id)
        if (
            bot
            and params.user
            and any(
                (
                    params.user.is_site_admin(),
                    params.user.is_himself(user=Identity(id=bot.owner)),
                )
            )
        ):
            return bot
        else:
            logger.error("bot %d not found by user %s", id, params.get_user_id())
            raise UserHasNotPermissionError()

    def get_bot_info(self, id: int, params: RequestParameters) -> Optional[BotIdentityDTO]:
        """
        Get user informations
        Permission: SADMIN, GADMIN (own group), USER (own user)

        Args:
            id: bot id
            params: request parameters

        Returns: bot informations and roles

        """
        bot = self.get_bot(id, params)
        if bot:
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
        else:
            raise UserNotFoundError()

    def get_all_bots_by_owner(self, owner: int, params: RequestParameters) -> List[Bot]:
        """
        Get by bo owned by a user
        Permission: SADMIN, USER (owner)

        Args:
            owner: bots owner id
            params: request parameters

        Returns: list of bot owned by user

        """
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_himself(Identity(id=owner)),
            )
        ):
            return self.bots.get_all_by_owner(owner)
        else:
            logger.error(
                "user %s has not permission to fetch bots owner=%d",
                params.get_user_id(),
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

    def get_all_groups(self, params: RequestParameters, details: bool = False) -> List[Union[GroupDetailDTO, GroupDTO]]:
        """
        Get all groups.
        Permission: SADMIN
        Args:
            params: request parameters
            details: get all user information, including users

        Returns: list of groups

        """
        if params.user:
            group_list = []

            if params.user.is_site_admin():
                group_list = self.groups.get_all()
            else:
                roles_by_user = self.roles.get_all_by_user(params.user.id)

                for role in roles_by_user:
                    if not details or role.type == RoleType.ADMIN:
                        tmp = self.groups.get(role.group_id)
                        if tmp:
                            group_list.append(tmp)
        else:
            logger.error(
                "user %s has not permission to get all groups",
                params.get_user_id(),
            )
            raise UserHasNotPermissionError()

        return (
            [grp for grp in [self.get_group_info(group.id, params) for group in group_list] if grp is not None]
            if details
            else [group.to_dto() for group in group_list]
        )

    def _get_user_by_group(self, group: str) -> List[Identity]:
        roles = self.roles.get_all_by_group(group)
        user_list = []
        for role in roles:
            user = self.get_identity(role.identity_id)
            if user:
                user_list.append(user)
        return user_list

    def get_all_users(
        self, params: RequestParameters, details: Optional[bool] = False
    ) -> List[Union[UserInfo, IdentityDTO]]:
        """
        Get all users.
        Permission: SADMIN
        Args:
            params: request parameters
            details: get all user information, including roles

        Returns: list of groups

        """
        if params.user:
            user_list = []
            roles = self.roles.get_all_by_user(params.user.id)
            groups = [r.group for r in roles]
            if any(
                (
                    params.user.is_site_admin(),
                    params.user.is_group_admin(groups),
                )
            ):
                user_list = self.ldap.get_all() + self.users.get_all()
            else:
                for group in groups:
                    user_list.extend([usr for usr in self._get_user_by_group(group.id) if usr not in user_list])

            return (
                [usr for usr in [self.get_user_info(user.id, params) for user in user_list] if usr is not None]
                if details
                else [user.to_dto() for user in user_list]
            )
        else:
            logger.error(
                "user %s has not permission to get all users",
                params.get_user_id(),
            )
            raise UserHasNotPermissionError()

    def get_all_bots(self, params: RequestParameters) -> List[Bot]:
        """
        Get all bots
        Permission: SADMIN
        Args:
            params: request parameters

        Returns:

        """
        if params.user and params.user.is_site_admin():
            return self.bots.get_all()
        else:
            logger.error(
                "user %s has not permission to get all bots",
                params.get_user_id(),
            )
            raise UserHasNotPermissionError()

    def get_all_roles_in_group(self, group: str, params: RequestParameters) -> List[Role]:
        """
        Get all roles inside a group
        Permission: SADMIN, GADMIN (own group)

        Args:
            group: group linked to role
            params: request parameters

        Returns: list of role

        """
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(Group(id=group)),
            )
        ):
            return self.roles.get_all_by_group(group)
        else:
            logger.error(
                "user %s has not permission to get all roles in group %s",
                params.get_user_id(),
                group,
            )
            raise UserHasNotPermissionError()

    def delete_group(self, id: str, params: RequestParameters) -> None:
        """
        Delete group
        Permission: SADMIN, GADMIN (own group)
        Args:
            id: group id to delete
            params: request parameters

        Returns:

        """
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(Group(id=id)),
            )
        ):
            for role in self.roles.get_all_by_group(group=id):
                self.roles.delete(user=role.identity_id, group=role.group_id)

            logger.info("group %s deleted by user %s", id, params.get_user_id())
            return self.groups.delete(id)
        else:
            logger.error(
                "user %s has not permission to delete group %s",
                params.get_user_id(),
                id,
            )
            raise UserHasNotPermissionError()

    def delete_user(self, id: int, params: RequestParameters) -> None:
        """
        Delete user
        Permission: SADMIN, USER (own user)
        Args:
            id: user id
            params: request parameters

        Returns:

        """
        if params.user and any((params.user.is_site_admin(), params.user.is_himself(User(id=id)))):
            for b in self.bots.get_all_by_owner(id):
                self.delete_bot(b.id, params)

            self.delete_all_roles_from_user(id, params)

            logger.info("user %s deleted by user %s", id, params.get_user_id())

            user = self.get_user(id, params)
            if isinstance(user, UserLdap):
                return self.ldap.delete(id)
            else:
                return self.users.delete(id)  # return for test purpose

        else:
            logger.info(
                "user %s has not permission to delete user %d",
                params.get_user_id(),
                id,
            )
            raise UserHasNotPermissionError()

    def delete_bot(self, id: int, params: RequestParameters) -> None:
        """
        Delete bot
        Permission: SADMIN, USER (owner)
        Args:
            id: bot id
            params: request parameters

        Returns:

        """
        bot = self.bots.get(id)
        if (
            params.user
            and bot
            and any(
                (
                    params.user.is_site_admin(),
                    params.user.is_himself(Identity(id=bot.owner)),
                )
            )
        ):
            logger.info("bot %d deleted by user %s", id, params.get_user_id())
            for role in self.roles.get_all_by_user(id):
                self.roles.delete(user=role.identity_id, group=role.group_id)
            return self.bots.delete(id)
        else:
            logger.error(
                "user %s has not permission to delete bot %d",
                params.get_user_id(),
                id,
            )
            raise UserHasNotPermissionError()

    def delete_role(self, user: int, group: str, params: RequestParameters) -> None:
        """
        Delete role
        Permission: SADMIN, GADMIN (own group)
        Args:
            user: user linked to role
            group: group linked to role
            params: request parameters

        Returns:

        """
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(Group(id=group)),
            )
        ):
            logger.info(
                "role (user=%d, group=%s) deleted by %s",
                user,
                group,
                params.get_user_id(),
            )
            return self.roles.delete(user, group)
        else:
            logger.error(
                "user %s has not permission to delete role (user=%d, group=%s)",
                params.get_user_id(),
                user,
                group,
            )
            raise UserHasNotPermissionError()

    def delete_all_roles_from_user(self, id: int, params: RequestParameters) -> int:
        """
        Delete all roles from a specific user
        Permission: SADMIN, GADMIN (own group)
        Args:
            id: user linked to roles
            params: request parameters

        Returns:

        """
        roles = self.roles.get_all_by_user(id)
        groups = [r.group for r in roles]

        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(groups),
            )
        ):
            for role in roles:
                self.roles.delete(role.identity_id, role.group_id)
            return id
        else:
            raise UserHasNotPermissionError()
