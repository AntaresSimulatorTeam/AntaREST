from http import HTTPStatus
from typing import Optional, Any

from fastapi import FastAPI
from fastapi_jwt_auth.exceptions import AuthJWTException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from starlette.requests import Request
from starlette.responses import JSONResponse

from antarest.common.config import Config
from antarest.common.interfaces.eventbus import IEventBus, DummyEventBusService
from antarest.login.ldap import LdapService
from antarest.login.repository import (
    UserRepository,
    GroupRepository,
    RoleRepository,
    BotRepository,
    UserLdapRepository,
)
from antarest.login.service import LoginService
from antarest.login.web import create_login_api


def build_login(
    application: FastAPI,
    config: Config,
    db_session: Session,
    service: Optional[LoginService] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> LoginService:
    """
    Login module linking dependency

    Args:
        application: flask application
        config: server configuration
        db_session: database session
        service: used by testing to inject mock. Let None to use true instantiation
        event_bus: used by testing to inject mock. Let None to use true instantiation

    Returns: user facade service

    """

    if service is None:
        user_repo = UserRepository(config, db_session)
        bot_repo = BotRepository(db_session)
        group_repo = GroupRepository(db_session)
        role_repo = RoleRepository(db_session)

        ldap_repo = UserLdapRepository(db_session)
        ldap = LdapService(users=ldap_repo, config=config)

        service = LoginService(
            user_repo=user_repo,
            bot_repo=bot_repo,
            group_repo=group_repo,
            role_repo=role_repo,
            ldap=ldap,
            event_bus=event_bus,
        )

    @application.exception_handler(AuthJWTException)
    def authjwt_exception_handler(
        request: Request, exc: AuthJWTException
    ) -> Any:
        return JSONResponse(
            status_code=HTTPStatus.UNAUTHORIZED,
            content={"detail": exc.message},
        )

    application.include_router(create_login_api(service, config))
    return service
