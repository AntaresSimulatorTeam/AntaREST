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

from typing import Any, Optional

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import DummyEventBusService, IEventBus
from antarest.core.serde.json import from_json
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.ldap import LdapService
from antarest.login.repository import (
    BotRepository,
    GroupRepository,
    IdentityRepository,
    RoleRepository,
    UserLdapRepository,
    UserRepository,
)
from antarest.login.service import LoginService

_login_service_ref: Optional[LoginService] = None


def set_login_service_for_denylist(service: LoginService) -> None:
    global _login_service_ref
    _login_service_ref = service


@AuthJWT.token_in_denylist_loader  # type: ignore
def check_if_token_is_revoked(decrypted_token: Any) -> bool:
    subject = from_json(decrypted_token["sub"])
    user_id = subject["id"]
    token_type = subject["type"]
    with db():
        return token_type == "bots" and _login_service_ref is not None and not _login_service_ref.exists_bot(user_id)


def build_login(
    config: Config,
    service: Optional[LoginService] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> LoginService:
    """
    Login module linking dependency

    Args:
        config: server configuration
        service: used by testing to inject mock. Let None to use true instantiation
        event_bus: used by testing to inject mock. Let None to use true instantiation

    Returns: user facade service

    """

    if service is None:
        user_repo = UserRepository()
        identity_repo = IdentityRepository()
        bot_repo = BotRepository()
        group_repo = GroupRepository()
        role_repo = RoleRepository()

        ldap_repo = UserLdapRepository()
        ldap = LdapService(config=config, users=ldap_repo, groups=group_repo, roles=role_repo)

        service = LoginService(
            user_repo=user_repo,
            identity_repo=identity_repo,
            bot_repo=bot_repo,
            group_repo=group_repo,
            role_repo=role_repo,
            ldap=ldap,
            event_bus=event_bus,
        )

    return service
