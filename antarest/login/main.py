from typing import Optional

from flask import Flask
from flask_jwt_extended import JWTManager  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

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
    application: Flask,
    config: Config,
    db_session: Session,
    service: Optional[LoginService] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> LoginService:

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

    jwt = JWTManager(application)
    application.register_blueprint(create_login_api(service, config, jwt))
    return service
