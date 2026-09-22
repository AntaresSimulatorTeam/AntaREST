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

from fastapi import APIRouter, Depends, HTTPException

from antarest.core.api_types import SanitizedStr
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.roles import RoleType
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.json import from_json
from antarest.core.utils.web import APITag
from antarest.dependencies import AuthDep, ConfigDep, LoginServiceDep, auth_required
from antarest.fastapi_jwt_auth import AuthJWT
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
from antarest.login.utils import get_user_id

logger = logging.getLogger(__name__)


class UserCredentials(AntaresBaseModel):
    username: SanitizedStr
    password: SanitizedStr


def _generate_tokens(user: JWTUser, jwt_manager: AuthJWT, expire: timedelta | None = None) -> CredentialsDTO:
    access_token = jwt_manager.create_access_token(subject=user.model_dump_json(), expires_time=expire)
    refresh_token = jwt_manager.create_refresh_token(subject=user.model_dump_json())
    return CredentialsDTO(
        user=user.id,
        access_token=access_token.decode() if isinstance(access_token, bytes) else access_token,
        refresh_token=refresh_token.decode() if isinstance(refresh_token, bytes) else refresh_token,
    )


def create_user_api() -> APIRouter:
    bp = APIRouter(prefix="/v1", tags=[APITag.users], dependencies=[Depends(auth_required)])

    @bp.get("/users")
    def users_get_all(service: LoginServiceDep, details: bool = False) -> list[IdentityDTO | UserInfo]:
        logger.info("Fetching users list")
        return service.get_all_users(details)

    @bp.get("/users/{id}")
    def users_get_id(service: LoginServiceDep, id: int, details: bool = False) -> IdentityDTO | UserInfo:
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
    def users_create(service: LoginServiceDep, create_user: UserCreateDTO) -> UserInfo:
        logger.info(f"Creating new user '{create_user.name}'")
        return service.create_user(create_user).to_dto()

    @bp.put("/users/{id}")
    def users_update(service: LoginServiceDep, id: int, user_info: UserInfo) -> UserInfo:
        logger.info(f"Updating user {id}")
        if id != user_info.id:
            raise HTTPException(status_code=400, detail="Id in path must be same id in body")
        return service.save_user(User.from_dto(user_info)).to_dto()

    @bp.delete("/users/{id}")
    def users_delete(service: LoginServiceDep, id: int) -> None:
        logger.info(f"Removing user {id}")
        service.delete_user(id)

    @bp.delete("/users/roles/{id}")
    def roles_delete_by_user(service: LoginServiceDep, id: int) -> None:
        logger.info(f"Removing user {id} roles")
        service.delete_all_roles_from_user(id)

    @bp.get("/groups")
    def groups_get_all(service: LoginServiceDep, details: bool = False) -> list[GroupDetailDTO | GroupDTO]:
        logger.info("Fetching groups list")
        return service.get_all_groups(details)

    @bp.get("/groups/{id}")
    def groups_get_id(service: LoginServiceDep, id: SanitizedStr, details: bool = False) -> GroupDetailDTO | GroupDTO:
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
    def groups_create(service: LoginServiceDep, group_dto: GroupCreationDTO) -> GroupDTO:
        logger.info(f"Creating new group '{group_dto.name}'")
        group = Group(
            id=group_dto.id,
            name=group_dto.name,
        )
        return service.save_group(group).to_dto()

    @bp.delete("/groups/{id}")
    def groups_delete(service: LoginServiceDep, id: SanitizedStr) -> None:
        logger.info(f"Removing group {id}")
        service.delete_group(id)

    @bp.get("/roles/group/{group}")
    def roles_get_all(service: LoginServiceDep, group: SanitizedStr) -> list[RoleDetailDTO]:
        logger.info(f"Fetching roles for group {group}")
        return [r.to_dto() for r in service.get_all_roles_in_group(group=group)]

    @bp.post("/roles")
    def role_create(service: LoginServiceDep, role: RoleCreationDTO) -> RoleDetailDTO:
        logger.info(f"Creating new role ({role.group_id},{role.type}) for {role.identity_id}")
        return service.save_role(role).to_dto()

    @bp.delete("/roles/{group}/{user}")
    def roles_delete(service: LoginServiceDep, user: int, group: SanitizedStr) -> None:
        logger.info(f"Remove role in group {group} for {user}")
        service.delete_role(user, group)

    @bp.post("/bots", summary="Create bot token")
    def bots_create(
        service: LoginServiceDep,
        create: BotCreateDTO,
        jwt_manager: AuthDep,
    ) -> str:
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
    def get_bot(service: LoginServiceDep, id: int, verbose: int | None = None) -> BotIdentityDTO | BotDTO:
        logger.info(f"Fetching bot {id}")
        bot = service.get_bot_info(id) if verbose else service.get_bot(id).to_dto()
        if not bot:
            raise UserHasNotPermissionError()
        return bot

    @bp.get(
        "/bots",
        summary="List all bots",
    )
    def get_all_bots(service: LoginServiceDep, owner: int | None = None) -> list[BotDTO]:
        logger.info(f"Fetching bot list for {owner or get_user_id()}")
        bots = service.get_all_bots_by_owner(owner) if owner else service.get_all_bots()
        return [b.to_dto() for b in bots]

    @bp.delete(
        "/bots/{id}",
        summary="Revoke bot token",
    )
    def bots_delete(service: LoginServiceDep, id: int) -> None:
        logger.info(f"Removing bot {id}")
        service.delete_bot(id)

    @bp.get("/auth", include_in_schema=False)
    def auth_needed(config: ConfigDep) -> bool:
        return not config.security.disabled

    return bp


def create_login_api() -> APIRouter:
    bp = APIRouter(prefix="/v1", tags=[APITag.users])

    @bp.post("/login", summary="Login")
    def login(
        service: LoginServiceDep,
        credentials: UserCredentials,
        jwt_manager: AuthDep,
    ) -> CredentialsDTO:
        logger.info(f"New login for {credentials.username}")
        user = service.authenticate(credentials.username, credentials.password)
        if not user:
            raise HTTPException(status_code=401, detail="Bad username or password")
        resp = _generate_tokens(user, jwt_manager)
        return resp

    @bp.post(
        "/refresh",
        summary="Refresh access token",
    )
    def refresh(service: LoginServiceDep, jwt_manager: AuthDep) -> CredentialsDTO:
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
