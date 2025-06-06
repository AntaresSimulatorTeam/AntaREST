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

import base64
import json
from datetime import timedelta
from pathlib import Path
from typing import Dict, Union
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.application import create_app_ctxt
from antarest.core.config import Config, SecurityConfig
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.main import build_login
from antarest.login.model import (
    Bot,
    BotCreateDTO,
    BotRoleCreateDTO,
    Group,
    GroupDTO,
    IdentityDTO,
    Password,
    Role,
    RoleDetailDTO,
    RoleType,
    User,
    UserCreateDTO,
    UserInfo,
)
from antarest.main import JwtSettings


def create_app(service: Mock, auth_disabled=False) -> FastAPI:
    app = FastAPI(title=__name__)

    @AuthJWT.load_config
    def get_config():
        return JwtSettings(
            authjwt_secret_key="super-secret",
            authjwt_token_location=("headers", "cookies"),
        )

    app_ctxt = create_app_ctxt(app)
    build_login(
        app_ctxt,
        service=service,
        config=Config(
            resources_path=Path(),
            security=SecurityConfig(disabled=auth_disabled),
        ),
    )
    return app_ctxt.build()


class TokenType:
    REFRESH: str = "REFRESH"
    ACCESS: str = "ACCESS"


def create_auth_token(
    app: FastAPI,
    expires_delta: Union[int, timedelta] = timedelta(days=2),
    type: TokenType = TokenType.ACCESS,
) -> Dict[str, str]:
    jwt_manager = AuthJWT()
    create_token = jwt_manager.create_access_token if type == TokenType.ACCESS else jwt_manager.create_refresh_token
    token = create_token(
        expires_time=expires_delta,
        subject=JWTUser(
            id=0,
            impersonator=0,
            type="users",
            groups=[JWTGroup(id="group", name="group", role=RoleType.ADMIN)],
        ).model_dump_json(),
    )
    return {"Authorization": f"Bearer {token if isinstance(token, str) else token.decode()}"}


@pytest.mark.unit_test
def test_auth_needed() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/v1/auth", headers=create_auth_token(app))
    assert res.status_code == 200

    res = client.get("/v1/auth")
    assert res.status_code == 401

    app = create_app(service, True)
    client = TestClient(app)
    res = client.get("/v1/auth")
    assert res.status_code == 200


@pytest.mark.unit_test
def test_auth() -> None:
    service = Mock()
    service.authenticate.return_value = JWTUser(id=0, type="user", impersonator=0)

    app = create_app(service)
    client = TestClient(app)
    res = client.post("/v1/login", json={"username": "admin", "password": "admin"})

    assert res.status_code == 200
    assert res.json()["access_token"]

    service.authenticate.assert_called_once_with("admin", "admin")


@pytest.mark.unit_test
def test_auth_fail() -> None:
    service = Mock()
    service.authenticate.return_value = None

    app = create_app(service)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post("/v1/login", json={"username": "admin", "password": "admin"})

    assert res.status_code == 401


@pytest.mark.unit_test
def test_expiration() -> None:
    service = Mock()
    service.get_user.return_value = JWTUser(id=0, type="user", impersonator=0)

    app = create_app(service)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get(
        "/v1/users",
        headers=create_auth_token(app, expires_delta=timedelta(days=-1)),
    )

    assert res.status_code == 401
    data = res.json()
    assert data["detail"] == "Signature has expired"


@pytest.mark.unit_test
def test_refresh() -> None:
    service = Mock()
    service.get_jwt.return_value = JWTUser(id=0, type="user", impersonator=0)

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/v1/refresh",
        headers=create_auth_token(app, type=TokenType.REFRESH),
    )

    assert res.status_code == 200
    data = res.json()
    meta, b64, sign = str(data["access_token"]).split(".")

    data = b64 + "==="  # fix padding issue
    json.loads(base64.b64decode(data))["sub"]


@pytest.mark.unit_test
def test_user() -> None:
    service = Mock()
    service.get_all_users.return_value = [UserInfo(id=1, name="user")]

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/users", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == [User(id=1, name="user").to_dto().model_dump()]


@pytest.mark.unit_test
def test_user_id() -> None:
    service = Mock()
    service.get_user.return_value = User(id=1, name="user")

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/users/1", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == User(id=1, name="user").to_dto().model_dump()


@pytest.mark.unit_test
def test_user_id_with_details() -> None:
    service = Mock()
    service.get_user_info.return_value = IdentityDTO(id=1, name="user", roles=[])

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/users/1?details=true", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == IdentityDTO(id=1, name="user", roles=[]).model_dump()


@pytest.mark.unit_test
def test_user_create() -> None:
    user = UserCreateDTO(name="a", password="b")
    user_id = User(id=0, name="a", password=Password("b"))
    service = Mock()
    service.create_user.return_value = user_id

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/v1/users",
        headers=create_auth_token(app),
        json=user.model_dump(),
    )

    assert res.status_code == 200
    service.create_user.assert_called_once_with(user)
    assert res.json() == user_id.to_dto().model_dump()


@pytest.mark.unit_test
def test_user_save() -> None:
    user = User(id=0, name="a", password=Password("b"))
    service = Mock()
    service.save_user.return_value = user

    app = create_app(service)
    client = TestClient(app)
    user_obj = user.to_dto().model_dump()
    res = client.put(
        "/v1/users/0",
        headers=create_auth_token(app),
        json=user_obj,
    )

    assert res.status_code == 200
    assert res.json() == user_obj

    assert service.save_user.call_count == 1
    call = service.save_user.call_args_list[0]
    assert call[0][0].to_dto().model_dump() == user_obj


@pytest.mark.unit_test
def test_user_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/v1/users/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_user.assert_called_once_with(0)


@pytest.mark.unit_test
def test_group() -> None:
    service = Mock()
    service.get_all_groups.return_value = [GroupDTO(id="my-group", name="group")]

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/groups", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == [Group(id="my-group", name="group").to_dto().model_dump()]


@pytest.mark.unit_test
def test_group_id() -> None:
    service = Mock()
    service.get_group.return_value = Group(id="my-group", name="group")

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/groups/1", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == Group(id="my-group", name="group").to_dto().model_dump()


@pytest.mark.unit_test
def test_group_create() -> None:
    group = Group(id="my-group", name="group")
    service = Mock()
    service.save_group.return_value = group

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/v1/groups",
        headers=create_auth_token(app),
        json={"name": "group"},
    )

    assert res.status_code == 200
    assert res.json() == group.to_dto().model_dump()


@pytest.mark.unit_test
def test_group_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    print(create_auth_token(app))
    res = client.delete("/v1/groups/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_group.assert_called_once_with("0")


@pytest.mark.unit_test
def test_role() -> None:
    role = Role(
        identity=User(id=0, name="n"),
        group=Group(id="g", name="n"),
        type=RoleType.ADMIN,
    )
    service = Mock()
    service.get_all_roles_in_group.return_value = [role]

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/roles/group/g", headers=create_auth_token(app))
    assert res.status_code == 200
    assert [RoleDetailDTO.model_validate(el) for el in res.json()] == [role.to_dto()]


@pytest.mark.unit_test
def test_role_create() -> None:
    role = Role(
        identity=User(id=0, name="n"),
        group=Group(id="g", name="n"),
        type=RoleType.ADMIN,
    )
    service = Mock()
    service.save_role.return_value = role

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/v1/roles",
        headers=create_auth_token(app),
        json={"type": RoleType.ADMIN.value, "identity_id": 0, "group_id": "g"},
    )

    assert res.status_code == 200
    assert RoleDetailDTO.model_validate(res.json()) == role.to_dto()


@pytest.mark.unit_test
def test_role_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/v1/roles/group/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_role.assert_called_once_with(0, "group")


@pytest.mark.unit_test
def test_roles_delete_by_user() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/v1/users/roles/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_all_roles_from_user.assert_called_once_with(0)


@pytest.mark.unit_test
def test_bot_create() -> None:
    bot = Bot(id=2, owner=3, name="bot", is_author=False)
    create = BotCreateDTO(
        name="bot",
        group="group",
        roles=[BotRoleCreateDTO(group="group", role=40)],
    )

    service = Mock()
    service.save_bot.return_value = bot
    service.get_group.return_value = Group(id="group", name="group")

    create.model_dump_json()
    app = create_app(service)
    client = TestClient(app)
    res = client.post("/v1/bots", headers=create_auth_token(app), json=create.model_dump())

    assert res.status_code == 200
    assert len(res.json().split(".")) == 3


@pytest.mark.unit_test
def test_bot() -> None:
    bot = Bot(id=0, owner=4, is_author=False, name="foo")
    service = Mock()
    service.get_bot.return_value = bot

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/bots/0", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == bot.to_dto().model_dump()


@pytest.mark.unit_test
def test_all_bots() -> None:
    bots = [Bot(id=0, owner=4, is_author=False, name="foo")]
    service = Mock()
    service.get_all_bots.return_value = bots
    service.get_all_bots_by_owner.return_value = bots

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/bots", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == [b.to_dto().model_dump() for b in bots]

    res = client.get("/v1/bots?owner=4", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == [b.to_dto().model_dump() for b in bots]

    service.get_all_bots.assert_called_once()
    service.get_all_bots_by_owner.assert_called_once()


@pytest.mark.unit_test
def test_bot_delete() -> None:
    service = Mock()

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/v1/bots/0", headers=create_auth_token(app))

    assert res.status_code == 200
    service.delete_bot.assert_called_once_with(0)
