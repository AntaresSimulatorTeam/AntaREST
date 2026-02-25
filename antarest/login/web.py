# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from antarest.core.api_types import SanitizedStr
from antarest.core.config import Config
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.roles import RoleType
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.json import from_json
from antarest.core.utils.web import APITag
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.auth import Auth
from antarest.login.model import (
    BotCreateDTO,
    BotDTO,
    BotIdentityDTO,
    CredentialsDTO,
    Group,
    GroupCreationDTO,
    GroupDetailDTO,
    GroupDTO,
    IdentityDTO,
    RoleCreationDTO,
    RoleDetailDTO,
    User,
    UserCreateDTO,
    UserInfo,
)
from antarest.login.service import LoginService
from antarest.login.utils import get_user_id

logger = logging.getLogger(__name__)


class UserCredentials(AntaresBaseModel):
    username: str
    password: str


def _generate_tokens(user: JWTUser, jwt_manager: AuthJWT, expire: Optional[timedelta] = None) -> CredentialsDTO:
    access_token = jwt_manager.create_access_token(subject=user.model_dump_json(), expires_time=expire)
    refresh_token = jwt_manager.create_refresh_token(subject=user.model_dump_json())
    return CredentialsDTO(
        user=user.id,
        access_token=access_token.decode() if isinstance(access_token, bytes) else access_token,
        refresh_token=refresh_token.decode() if isinstance(refresh_token, bytes) else refresh_token,
    )


def create_user_api(service: LoginService, config: Config) -> APIRouter:
    """
    Endpoints user implementation

    Args:
        service: login facade service
        config: server config

    Returns:
        user endpoints
    """
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", tags=[APITag.users], dependencies=[auth.required()])

    @bp.get("/users")
    def users_get_all(details: bool = False) -> list[IdentityDTO | UserInfo]:
        logger.info("Fetching users list")
        return service.get_all_users(details)

    @bp.get("/users/{id}")
    def users_get_id(id: int, details: bool = False) -> IdentityDTO | UserInfo:
        logger.info(f"Fetching user info for {id}")
        u: IdentityDTO | UserInfo | None = None
        if details:
            u = service.get_user_info(id)
        else:
            ou = service.get_user(id)
            if ou:
                u = ou.to_dto()
        if u:
            return u
        else:
            raise HTTPException(status_code=404)

    @bp.post("/users")
    def users_create(create_user: UserCreateDTO) -> UserInfo:
        logger.info(f"Creating new user '{create_user.name}'")

        return service.create_user(create_user).to_dto()

    @bp.put("/users/{id}")
    def users_update(id: int, user_info: UserInfo) -> UserInfo:
        logger.info(f"Updating user {id}")

        if id != user_info.id:
            raise HTTPException(status_code=400, detail="Id in path must be same id in body")

        return service.save_user(User.from_dto(user_info)).to_dto()

    @bp.delete("/users/{id}")
    def users_delete(id: int) -> None:
        logger.info(f"Removing user {id}")
        service.delete_user(id)

    @bp.delete("/users/roles/{id}")
    def roles_delete_by_user(id: int) -> None:
        logger.info(f"Removing user {id} roles")
        service.delete_all_roles_from_user(id)

    @bp.get(
        "/groups",
    )
    def groups_get_all(details: bool = False) -> list[GroupDetailDTO | GroupDTO]:
        logger.info("Fetching groups list")
        return service.get_all_groups(details)

    @bp.get("/groups/{id}")
    def groups_get_id(id: SanitizedStr, details: bool = False) -> GroupDetailDTO | GroupDTO:
        logger.info(f"Fetching group {id} info")
        group: GroupDetailDTO | GroupDTO | None = None
        if details:
            group = service.get_group_info(id)
        else:
            optional_group = service.get_group(id)
            if optional_group:
                group = optional_group.to_dto()
        if group:
            return group
        else:
            raise HTTPException(status_code=404, detail=f"Group {id} not found")

    @bp.post("/groups")
    def groups_create(group_dto: GroupCreationDTO) -> GroupDTO:
        logger.info(f"Creating new group '{group_dto.name}'")
        group = Group(
            id=group_dto.id,
            name=group_dto.name,
        )
        return service.save_group(group).to_dto()

    @bp.delete("/groups/{id}")
    def groups_delete(id: SanitizedStr) -> None:
        logger.info(f"Removing group {id}")
        service.delete_group(id)

    @bp.get("/roles/group/{group}")
    def roles_get_all(group: SanitizedStr) -> list[RoleDetailDTO]:
        logger.info(f"Fetching roles for group {group}")
        return [r.to_dto() for r in service.get_all_roles_in_group(group=group)]

    @bp.post("/roles")
    def role_create(role: RoleCreationDTO) -> RoleDetailDTO:
        logger.info(f"Creating new role ({role.group_id},{role.type}) for {role.identity_id}")
        return service.save_role(role).to_dto()

    @bp.delete("/roles/{group}/{user}")
    def roles_delete(user: int, group: SanitizedStr) -> None:
        logger.info(f"Remove role in group {group} for {user}")
        service.delete_role(user, group)

    @bp.post("/bots", summary="Create bot token")
    def bots_create(create: BotCreateDTO, jwt_manager: AuthJWT = Depends()) -> str:
        logger.info(f"Creating new bot '{create.name}'")
        bot = service.save_bot(create)
        groups = []
        for role in create.roles:
            group = service.get_group(role.group)
            if not group:
                raise UserHasNotPermissionError()
            jwt_group = JWTGroup(
                id=group.id,
                name=group.name,
                role=RoleType(role.role),
            )
            groups.append(jwt_group)

        jwt = JWTUser(
            id=bot.id,
            impersonator=bot.get_impersonator(),
            type=bot.type,
            groups=groups,
        )
        tokens = _generate_tokens(jwt, jwt_manager, expire=timedelta(days=368 * 200))
        return tokens.access_token

    @bp.get("/bots/{id}")
    def get_bot(id: int, verbose: Optional[int] = None) -> BotIdentityDTO | BotDTO:
        logger.info(f"Fetching bot {id}")
        bot = service.get_bot_info(id) if verbose else service.get_bot(id).to_dto()
        if not bot:
            raise UserHasNotPermissionError()
        return bot

    @bp.get(
        "/bots",
        summary="List all bots",
    )
    def get_all_bots(owner: Optional[int] = None) -> list[BotDTO]:
        logger.info(f"Fetching bot list for {owner or get_user_id()}")

        bots = service.get_all_bots_by_owner(owner) if owner else service.get_all_bots()
        return [b.to_dto() for b in bots]

    @bp.delete(
        "/bots/{id}",
        summary="Revoke bot token",
    )
    def bots_delete(id: int) -> None:
        logger.info(f"Removing bot {id}")
        service.delete_bot(id)

    @bp.get("/auth", include_in_schema=False)
    def auth_needed() -> bool:
        return not config.security.disabled

    return bp


def create_login_api(service: LoginService) -> APIRouter:
    """
    Endpoints login implementation

    Args:
        service: login facade service

    Returns:
        login endpoints
    """
    bp = APIRouter(prefix="/v1", tags=[APITag.users])

    @bp.post("/login", summary="Login")
    def login(
        credentials: UserCredentials,
        jwt_manager: AuthJWT = Depends(),
    ) -> CredentialsDTO:
        logger.info(f"New login for {credentials.username}")
        user = service.authenticate(credentials.username, credentials.password)
        if not user:
            raise HTTPException(status_code=401, detail="Bad username or password")

        # Identity can be any data that is json serializable
        resp = _generate_tokens(user, jwt_manager)

        return resp

    @bp.post(
        "/refresh",
        summary="Refresh access token",
    )
    def refresh(jwt_manager: AuthJWT = Depends()) -> CredentialsDTO:
        jwt_manager.jwt_refresh_token_required()
        identity = from_json(jwt_manager.get_jwt_subject())
        logger.debug(f"Refreshing access token for {identity['id']}")
        user = service.get_jwt(identity["id"])
        if user:
            resp = _generate_tokens(user, jwt_manager)

            return resp
        else:
            raise HTTPException(status_code=403, detail="Token invalid")

    return bp
