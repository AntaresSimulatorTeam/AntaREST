import json
from datetime import timedelta
from typing import Any, Optional

from fastapi import Depends, APIRouter, Form, HTTPException, Query
from fastapi_jwt_auth import AuthJWT  # type: ignore
from markupsafe import escape
from pydantic import BaseModel
from starlette.responses import JSONResponse

from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.login.auth import Auth
from antarest.common.config import Config
from antarest.login.model import (
    User,
    Group,
    Password,
    Role,
    BotCreateDTO,
    UserCreateDTO,
    RoleDTO,
    RoleCreationDTO,
    UserInfo,
    GroupDTO,
)
from antarest.login.service import LoginService


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
    bp = APIRouter()

    auth = Auth(config)

    def generate_tokens(
        user: JWTUser, jwt_manager: AuthJWT, expire: Optional[timedelta] = None
    ) -> Any:
        access_token = jwt_manager.create_access_token(
            subject=json.dumps(user.to_dict()), expires_time=expire
        )
        refresh_token = jwt_manager.create_refresh_token(
            subject=json.dumps(user.to_dict())
        )
        return {
            "user": user.id,
            "access_token": access_token.decode()
            if isinstance(access_token, bytes)
            else access_token,
            "refresh_token": refresh_token.decode()
            if isinstance(refresh_token, bytes)
            else refresh_token,
        }

    @AuthJWT.token_in_denylist_loader  # type: ignore
    def check_if_token_is_revoked(decrypted_token: Any) -> bool:
        subject = json.loads(decrypted_token["sub"])
        user_id = subject["id"]
        token_type = subject["type"]
        return token_type == "bots" and not service.exists_bot(user_id)

    @bp.post("/login", tags=["User"], summary="Login")
    def login(
        credentials: UserCredentials,
        jwt_manager: AuthJWT = Depends(),
    ) -> Any:
        user = service.authenticate(credentials.username, credentials.password)
        if not user:
            raise HTTPException(
                status_code=401, detail="Bad username or password"
            )

        # Identity can be any data that is json serializable
        resp = generate_tokens(user, jwt_manager)

        return resp

    @bp.post("/refresh", tags=["User"], summary="Refresh access token")
    def refresh(jwt_manager: AuthJWT = Depends()) -> Any:
        jwt_manager.jwt_refresh_token_required()
        identity = json.loads(jwt_manager.get_jwt_subject())
        user = service.get_jwt(identity["id"])
        if user:
            resp = generate_tokens(user, jwt_manager)

            return resp
        else:
            raise HTTPException(status_code=403, detail="Token invalid")

    @bp.get("/users", tags=["User"])
    def users_get_all(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        return [u.to_dict() for u in service.get_all_users(params)]

    @bp.get("/users/{id}", tags=["User"])
    def users_get_id(
        id: int, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        params = RequestParameters(user=current_user)
        u = service.get_user_info(id, params)
        if u:
            return u.to_dict()
        else:
            raise HTTPException(status_code=404)

    @bp.post("/users", tags=["User"])
    def users_create(
        create_user: UserCreateDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)

        return service.create_user(create_user, params).to_dict()

    @bp.put("/users/{id}", tags=["User"])
    def users_update(
        id: int,
        user_info: UserInfo,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)

        if id != user_info.id:
            raise HTTPException(
                status_code=400, detail="Id in path must be same id in body"
            )

        return service.save_user(User.from_dto(user_info), params).to_dict()

    @bp.delete("/users/{id}", tags=["User"])
    def users_delete(
        id: int, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        params = RequestParameters(user=current_user)
        service.delete_user(id, params)
        return id

    @bp.delete("/users/roles/{id}", tags=["User"])
    def roles_delete_by_user(
        id: int, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        params = RequestParameters(user=current_user)
        service.delete_all_roles_from_user(id, params)
        return id

    @bp.get("/groups", tags=["User"])
    def groups_get_all(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        return [g.to_dict() for g in service.get_all_groups(params)]

    @bp.get("/groups/{id}", tags=["User"])
    def groups_get_id(
        id: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        gid = str(escape(id))
        params = RequestParameters(user=current_user)
        group = service.get_group(gid, params)
        if group:
            return group.to_dict()
        else:
            return HTTPException(
                status_code=404, detail=f"Group {gid} not found"
            )

    @bp.post("/groups", tags=["User"])
    def groups_create(
        group_dto: GroupDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        group = Group(id=group_dto.id, name=group_dto.name)
        return service.save_group(group, params).to_dict()

    @bp.delete("/groups/{id}", tags=["User"])
    def groups_delete(
        id: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        gid = str(escape(id))
        params = RequestParameters(user=current_user)
        service.delete_group(gid, params)
        return id

    @bp.get("/roles/group/{group}", tags=["User"])
    def roles_get_all(
        group: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        group = str(escape(group))
        params = RequestParameters(user=current_user)
        return [
            r.to_dict()
            for r in service.get_all_roles_in_group(group=group, params=params)
        ]

    @bp.post("/roles", tags=["User"])
    def role_create(
        role: RoleCreationDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        return service.save_role(role, params).to_dict()

    @bp.delete("/roles/{group}/{user}", tags=["User"])
    def roles_delete(
        user: int,
        group: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        group = str(escape(group))
        params = RequestParameters(user=current_user)
        service.delete_role(user, group, params)
        return user, group

    @bp.post("/bots", tags=["User"], summary="Create bot token")
    def bots_create(
        create: BotCreateDTO,
        jwt_manager: AuthJWT = Depends(),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        bot = service.save_bot(create, params)

        if not bot:
            return UserHasNotPermissionError()

        group = service.get_group(create.group, params)
        if not group:
            return UserHasNotPermissionError()

        jwt = JWTUser(
            id=bot.id,
            impersonator=bot.get_impersonator(),
            type=bot.type,
            groups=[JWTGroup(id=group.id, name=group.name, role=create.role)],
        )
        tokens = generate_tokens(
            jwt, jwt_manager, expire=timedelta(days=368 * 200)
        )
        return tokens["access_token"]

    @bp.get("/bots/{id}", tags=["User"])
    def get_bot(
        id: int, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        params = RequestParameters(user=current_user)
        bot = service.get_bot(id, params)
        return bot.to_dict()

    @bp.get("/bots", tags=["User"])
    def get_all_bots(
        owner: Optional[int] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)

        bots = (
            service.get_all_bots_by_owner(owner, params)
            if owner
            else service.get_all_bots(params)
        )
        return [b.to_dict() for b in bots]

    @bp.delete("/bots/{id}", tags=["User"], summary="Revoke bot token")
    def bots_delete(
        id: int, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
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
        return JSONResponse(current_user.to_dict())

    return bp
