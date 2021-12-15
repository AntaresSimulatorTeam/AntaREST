import json
import logging
from datetime import timedelta
from typing import Any, Optional, List, Union, Tuple

from fastapi import Depends, APIRouter, HTTPException
from fastapi_jwt_auth import AuthJWT  # type: ignore
from markupsafe import escape  # type: ignore
from pydantic import BaseModel

from antarest.core.config import Config
from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.core.roles import RoleType
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.login.model import (
    User,
    Group,
    BotCreateDTO,
    UserCreateDTO,
    RoleCreationDTO,
    UserInfo,
    GroupDTO,
    CredentialsDTO,
    BotDTO,
    BotIdentityDTO,
    RoleDetailDTO,
    UserGroup,
    IdentityDTO,
)
from antarest.login.service import LoginService

logger = logging.getLogger(__name__)


class UserCredentials(BaseModel):
    username: str
    password: str


def create_login_api(service: LoginService, config: Config) -> APIRouter:
    """
    Endpoints login implementation
    Args:
        service: login facade service
        config: server config
        jwt: jwt manager

    Returns:

    """
    bp = APIRouter(prefix="/v1")

    auth = Auth(config)

    def generate_tokens(
        user: JWTUser, jwt_manager: AuthJWT, expire: Optional[timedelta] = None
    ) -> CredentialsDTO:
        access_token = jwt_manager.create_access_token(
            subject=user.json(), expires_time=expire
        )
        refresh_token = jwt_manager.create_refresh_token(subject=user.json())
        return CredentialsDTO(
            user=user.id,
            access_token=access_token.decode()
            if isinstance(access_token, bytes)
            else access_token,
            refresh_token=refresh_token.decode()
            if isinstance(refresh_token, bytes)
            else refresh_token,
        )

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
            raise HTTPException(
                status_code=401, detail="Bad username or password"
            )

        # Identity can be any data that is json serializable
        resp = generate_tokens(user, jwt_manager)

        return resp

    @bp.post(
        "/refresh",
        tags=[APITag.users],
        summary="Refresh access token",
        response_model=CredentialsDTO,
    )
    def refresh(jwt_manager: AuthJWT = Depends()) -> Any:
        jwt_manager.jwt_refresh_token_required()
        identity = json.loads(jwt_manager.get_jwt_subject())
        logger.debug(f"Refreshing access token for {identity['id']}")
        user = service.get_jwt(identity["id"])
        if user:
            resp = generate_tokens(user, jwt_manager)

            return resp
        else:
            raise HTTPException(status_code=403, detail="Token invalid")

    @bp.get("/users", tags=[APITag.users], response_model=List[UserInfo])
    def users_get_all(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching users list", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        return [u.to_dto() for u in service.get_all_users(params)]

    @bp.get(
        "/users/{id}",
        tags=[APITag.users],
        response_model=Union[IdentityDTO, UserInfo],  # type: ignore
    )
    def users_get_id(
        id: int,
        details: Optional[bool] = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching user info for {id}", extra={"user": current_user.id}
        )
        params = RequestParameters(user=current_user)
        u: Any = None
        if details:
            u = service.get_user_info(id, params)
        else:
            ou = service.get_user(id, params)
            if ou:
                u = ou.to_dto()
        if u:
            return u
        else:
            raise HTTPException(status_code=404)

    @bp.post("/users", tags=[APITag.users], response_model=UserInfo)
    def users_create(
        create_user: UserCreateDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new user '{create_user.name}'",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)

        return service.create_user(create_user, params).to_dto()

    @bp.put("/users/{id}", tags=[APITag.users], response_model=UserInfo)
    def users_update(
        id: int,
        user_info: UserInfo,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Updating user {id}", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)

        if id != user_info.id:
            raise HTTPException(
                status_code=400, detail="Id in path must be same id in body"
            )

        return service.save_user(User.from_dto(user_info), params).to_dto()

    @bp.delete("/users/{id}", tags=[APITag.users])
    def users_delete(
        id: int, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(f"Removing user {id}", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        service.delete_user(id, params)
        return id

    @bp.delete("/users/roles/{id}", tags=[APITag.users])
    def roles_delete_by_user(
        id: int, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(
            f"Removing user {id} roles", extra={"user": current_user.id}
        )
        params = RequestParameters(user=current_user)
        service.delete_all_roles_from_user(id, params)
        return id

    @bp.get("/groups", tags=[APITag.users], response_model=List[GroupDTO])
    def groups_get_all(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching groups list", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        return [g.to_dto() for g in service.get_all_groups(params)]

    @bp.get(
        "/groups/{id}",
        tags=[APITag.users],
        response_model=Union[UserGroup, GroupDTO],  # type: ignore
    )
    def groups_get_id(
        id: str,
        details: Optional[bool] = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching group {id} info", extra={"user": current_user.id}
        )
        params = RequestParameters(user=current_user)
        group: Any = None
        if details:
            group = service.get_group_info(id, params)
        else:
            optional_group = service.get_group(id, params)
            if optional_group:
                group = optional_group.to_dto()
        if group:
            return group
        else:
            return HTTPException(
                status_code=404, detail=f"Group {id} not found"
            )

    @bp.post("/groups", tags=[APITag.users], response_model=GroupDTO)
    def groups_create(
        group_dto: GroupDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new group '{group_dto.name}'",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        group = Group(
            id=escape(group_dto.id) if group_dto.id else None,
            name=group_dto.name,
        )
        return service.save_group(group, params).to_dto()

    @bp.delete("/groups/{id}", tags=[APITag.users], response_model=str)
    def groups_delete(
        id: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(f"Removing group {id}", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        service.delete_group(id, params)
        return id

    @bp.get(
        "/roles/group/{group}",
        tags=[APITag.users],
        response_model=List[RoleDetailDTO],
    )
    def roles_get_all(
        group: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(
            f"Fetching roles for group {group}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return [
            r.to_dto()
            for r in service.get_all_roles_in_group(group=group, params=params)
        ]

    @bp.post("/roles", tags=[APITag.users], response_model=RoleDetailDTO)
    def role_create(
        role: RoleCreationDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new role ({role.group_id},{role.type}) for {role.identity_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return service.save_role(role, params).to_dto()

    @bp.delete(
        "/roles/{group}/{user}",
        tags=[APITag.users],
    )
    def roles_delete(
        user: int,
        group: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Remove role in group {group} for {user}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        service.delete_role(user, group, params)
        return user, group

    @bp.post("/bots", tags=[APITag.users], summary="Create bot token")
    def bots_create(
        create: BotCreateDTO,
        jwt_manager: AuthJWT = Depends(),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new bot '{create.name}'",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        bot = service.save_bot(create, params)
        groups = []
        for role in create.roles:
            group = service.get_group(role.group, params)
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
        tokens = generate_tokens(
            jwt, jwt_manager, expire=timedelta(days=368 * 200)
        )
        return tokens.access_token

    @bp.get(
        "/bots/{id}",
        tags=[APITag.users],
        response_model=Union[BotIdentityDTO, BotDTO],  # type: ignore
    )
    def get_bot(
        id: int,
        verbose: Optional[int] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching bot {id}", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        bot = (
            service.get_bot_info(id, params)
            if verbose
            else service.get_bot(id, params).to_dto()
        )
        if not bot:
            return UserHasNotPermissionError()
        return bot

    @bp.get(
        "/bots",
        tags=[APITag.users],
        summary="List all bots",
        response_model=List[BotDTO],
    )
    def get_all_bots(
        owner: Optional[int] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching bot list for {owner or current_user.id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)

        bots = (
            service.get_all_bots_by_owner(owner, params)
            if owner
            else service.get_all_bots(params)
        )
        return [b.to_dto() for b in bots]

    @bp.delete(
        "/bots/{id}",
        tags=[APITag.users],
        summary="Revoke bot token",
        response_model=int,
    )
    def bots_delete(
        id: int, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(f"Removing bot {id}", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        service.delete_bot(id, params)
        return id

    @bp.get("/protected", include_in_schema=False)
    def protected(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        return f"user id={current_user.id}"

    @bp.get("/auth", include_in_schema=False)
    def auth_needed(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        return current_user

    return bp
