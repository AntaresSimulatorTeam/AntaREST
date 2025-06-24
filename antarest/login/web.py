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
from datetime import timedelta
from typing import Any, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException

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
    bp = APIRouter(prefix="/v1", dependencies=[auth.required()])

    @bp.get(
        "/users",
        tags=[APITag.users],
        response_model=List[Union[IdentityDTO, UserInfo]],
    )
    def users_get_all(details: bool = False) -> Any:
        logger.info("Fetching users list")
        return service.get_all_users(details)

    @bp.get("/users/{id}", tags=[APITag.users], response_model=Union[IdentityDTO, UserInfo])
    def users_get_id(id: int, details: bool = False) -> Any:
        logger.info(f"Fetching user info for {id}")
        u: Any = None
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

    @bp.post("/users", tags=[APITag.users], response_model=UserInfo)
    def users_create(create_user: UserCreateDTO) -> Any:
        logger.info(f"Creating new user '{create_user.name}'")

        return service.create_user(create_user).to_dto()

    @bp.put("/users/{id}", tags=[APITag.users], response_model=UserInfo)
    def users_update(id: int, user_info: UserInfo) -> Any:
        logger.info(f"Updating user {id}")

        if id != user_info.id:
            raise HTTPException(status_code=400, detail="Id in path must be same id in body")

        return service.save_user(User.from_dto(user_info)).to_dto()

    @bp.delete("/users/{id}", tags=[APITag.users])
    def users_delete(id: int) -> Any:
        logger.info(f"Removing user {id}")
        service.delete_user(id)
        return id

    @bp.delete("/users/roles/{id}", tags=[APITag.users])
    def roles_delete_by_user(id: int) -> Any:
        logger.info(f"Removing user {id} roles")
        service.delete_all_roles_from_user(id)
        return id

    @bp.get(
        "/groups",
        tags=[APITag.users],
        response_model=List[Union[GroupDetailDTO, GroupDTO]],
    )
    def groups_get_all(details: bool = False) -> Any:
        logger.info("Fetching groups list")
        return service.get_all_groups(details)

    @bp.get("/groups/{id}", tags=[APITag.users], response_model=Union[GroupDetailDTO, GroupDTO])
    def groups_get_id(id: str, details: bool = False) -> Any:
        logger.info(f"Fetching group {id} info")
        group: Any = None
        if details:
            group = service.get_group_info(id)
        else:
            optional_group = service.get_group(id)
            if optional_group:
                group = optional_group.to_dto()
        if group:
            return group
        else:
            return HTTPException(status_code=404, detail=f"Group {id} not found")

    @bp.post("/groups", tags=[APITag.users], response_model=GroupDTO)
    def groups_create(group_dto: GroupCreationDTO) -> Any:
        logger.info(f"Creating new group '{group_dto.name}'")
        group = Group(
            id=group_dto.id if group_dto.id else None,
            name=group_dto.name,
        )
        return service.save_group(group).to_dto()

    @bp.delete("/groups/{id}", tags=[APITag.users], response_model=str)
    def groups_delete(id: str) -> Any:
        logger.info(f"Removing group {id}")
        service.delete_group(id)
        return id

    @bp.get(
        "/roles/group/{group}",
        tags=[APITag.users],
        response_model=List[RoleDetailDTO],
    )
    def roles_get_all(group: str) -> Any:
        logger.info(f"Fetching roles for group {group}")
        return [r.to_dto() for r in service.get_all_roles_in_group(group=group)]

    @bp.post("/roles", tags=[APITag.users], response_model=RoleDetailDTO)
    def role_create(role: RoleCreationDTO) -> Any:
        logger.info(f"Creating new role ({role.group_id},{role.type}) for {role.identity_id}")
        return service.save_role(role).to_dto()

    @bp.delete(
        "/roles/{group}/{user}",
        tags=[APITag.users],
    )
    def roles_delete(user: int, group: str) -> Any:
        logger.info(f"Remove role in group {group} for {user}")
        service.delete_role(user, group)
        return user, group

    @bp.post("/bots", tags=[APITag.users], summary="Create bot token")
    def bots_create(create: BotCreateDTO, jwt_manager: AuthJWT = Depends()) -> Any:
        logger.info(f"Creating new bot '{create.name}'")
        bot = service.save_bot(create)
        groups = []
        for role in create.roles:
            group = service.get_group(role.group)
            if not group:
                return UserHasNotPermissionError()
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

    @bp.get("/bots/{id}", tags=[APITag.users], response_model=Union[BotIdentityDTO, BotDTO])
    def get_bot(id: int, verbose: Optional[int] = None) -> Any:
        logger.info(f"Fetching bot {id}")
        bot = service.get_bot_info(id) if verbose else service.get_bot(id).to_dto()
        if not bot:
            return UserHasNotPermissionError()
        return bot

    @bp.get(
        "/bots",
        tags=[APITag.users],
        summary="List all bots",
        response_model=List[BotDTO],
    )
    def get_all_bots(owner: Optional[int] = None) -> Any:
        logger.info(f"Fetching bot list for {owner or get_user_id()}")

        bots = service.get_all_bots_by_owner(owner) if owner else service.get_all_bots()
        return [b.to_dto() for b in bots]

    @bp.delete(
        "/bots/{id}",
        tags=[APITag.users],
        summary="Revoke bot token",
        response_model=int,
    )
    def bots_delete(id: int) -> Any:
        logger.info(f"Removing bot {id}")
        service.delete_bot(id)
        return id

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
    bp = APIRouter(prefix="/v1")

    @bp.post(
        "/login",
        tags=[APITag.users],
        summary="Login",
        response_model=CredentialsDTO,
    )
    def login(
        credentials: UserCredentials,
        jwt_manager: AuthJWT = Depends(),
    ) -> Any:
        logger.info(f"New login for {credentials.username}")
        user = service.authenticate(credentials.username, credentials.password)
        if not user:
            raise HTTPException(status_code=401, detail="Bad username or password")

        # Identity can be any data that is json serializable
        resp = _generate_tokens(user, jwt_manager)

        return resp

    @bp.post(
        "/refresh",
        tags=[APITag.users],
        summary="Refresh access token",
        response_model=CredentialsDTO,
    )
    def refresh(jwt_manager: AuthJWT = Depends()) -> Any:
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
