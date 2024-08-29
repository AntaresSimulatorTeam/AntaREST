import json
from http import HTTPStatus
from typing import Any, Optional

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import DummyEventBusService, IEventBus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.fastapi_jwt_auth.exceptions import AuthJWTException
from antarest.login.ldap import LdapService
from antarest.login.repository import BotRepository, GroupRepository, RoleRepository, UserLdapRepository, UserRepository
from antarest.login.service import LoginService
from antarest.login.web import create_login_api


def build_login(
    application: Optional[FastAPI],
    config: Config,
    service: Optional[LoginService] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> LoginService:
    """
    Login module linking dependency

    Args:
        application: flask application
        config: server configuration
        service: used by testing to inject mock. Let None to use true instantiation
        event_bus: used by testing to inject mock. Let None to use true instantiation

    Returns: user facade service

    """

    if service is None:
        user_repo = UserRepository()
        bot_repo = BotRepository()
        group_repo = GroupRepository()
        role_repo = RoleRepository()

        ldap_repo = UserLdapRepository()
        ldap = LdapService(config=config, users=ldap_repo, groups=group_repo, roles=role_repo)

        service = LoginService(
            user_repo=user_repo,
            bot_repo=bot_repo,
            group_repo=group_repo,
            role_repo=role_repo,
            ldap=ldap,
            event_bus=event_bus,
        )

    if application:

        @application.exception_handler(AuthJWTException)
        def authjwt_exception_handler(request: Request, exc: AuthJWTException) -> Any:
            return JSONResponse(
                status_code=HTTPStatus.UNAUTHORIZED,
                content={"detail": exc.message},
            )

    @AuthJWT.token_in_denylist_loader  # type: ignore
    def check_if_token_is_revoked(decrypted_token: Any) -> bool:
        subject = json.loads(decrypted_token["sub"])
        user_id = subject["id"]
        token_type = subject["type"]
        with db():
            return token_type == "bots" and service is not None and not service.exists_bot(user_id)

    if application:
        application.include_router(create_login_api(service, config))
    return service
