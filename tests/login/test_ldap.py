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

import json
import threading
import typing as t
from http.server import BaseHTTPRequestHandler, HTTPServer

from sqlalchemy import create_engine

from antarest.core.config import Config, ExternalAuthConfig, SecurityConfig
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.dbmodel import Base
from antarest.login.ldap import AuthDTO, ExternalUser, LdapService
from antarest.login.model import UserLdap
from antarest.login.repository import GroupRepository, RoleRepository, UserLdapRepository


class MockHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    This HTTP request handler simulates an LDAP server.
    """

    def log_request(self, code="-", size="-"):
        """Override the log_request method to suppress access logs"""

    # noinspection PyPep8Naming
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        data = self.rfile.read(content_length)

        if "/auth" in self.path:
            create = AuthDTO.from_json(json.loads(data))
            if create.user == "ext_id":
                # Simulate a known user
                ext_user = ExternalUser(
                    external_id=create.user,
                    first_name="John",
                    last_name="Smith",
                    groups={
                        "groupA": "some group name",
                        "groupB": "some other group name",
                        "groupC": "isGroupD",
                    },
                )
                res = json.dumps(ext_user.to_json(), ensure_ascii=False).encode("utf-8")
                self.send_response(200)

            else:
                # Simulate an unknown user
                res = "null".encode("utf-8")
                # response code is 401 (unauthorized) to simulate a wrong password
                self.send_response(401)

            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Content-Length", f"{len(res)}")
            self.end_headers()
            self.wfile.write(res)

        else:
            res = "Not found: {self.path}".encode("utf-8")
            self.send_response(404)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", f"{len(res)}")
            self.end_headers()
            self.wfile.write(res)


class TestLdapService:
    """
    Test the LDAP service
    """

    def test_login(self):
        # Create an in-memory database for this test.
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        # noinspection SpellCheckingInspection
        DBSessionMiddleware(
            None,
            custom_engine=engine,
            session_args={"autocommit": False, "autoflush": False},
        )

        # Start a mocked LDAP server in a dedicated thread.
        server_address = ("", 8869)  # port 8869 is the default port for LDAP
        httpd = HTTPServer(server_address, MockHTTPRequestHandler)
        server = threading.Thread(None, httpd.serve_forever, daemon=True)
        server.start()

        try:
            with db():
                ldap_repo = UserLdapRepository()
                group_repo = GroupRepository()
                role_repo = RoleRepository()

                config = Config(
                    security=SecurityConfig(
                        external_auth=ExternalAuthConfig(
                            url="http://localhost:8869",
                            default_group_role=RoleType.WRITER,
                            add_ext_groups=True,
                            group_mapping={"groupC": "D"},
                        )
                    )
                )

                ldap_service = LdapService(config=config, users=ldap_repo, groups=group_repo, roles=role_repo)

                # An unknown user cannot log in
                user: t.Optional[UserLdap] = ldap_service.login(name="unknown", password="pwd")
                assert user is None

                # A known user can log in
                user: t.Optional[UserLdap] = ldap_service.login(name="ext_id", password="pwd")
                assert user
                assert user.name == "John Smith"
                assert user.external_id == "ext_id"
                assert user.firstname == "John"
                assert user.lastname == "Smith"
                assert user.id

                # The user can be retrieved from the database
                assert ldap_repo.get(user.id) == user

                # Check that groups have been created
                roles = role_repo.get_all_by_user(user.id)
                assert len(roles) == 3

                # all roles have the same user and role type
                assert all(r.identity == user for r in roles)
                assert all(r.type == RoleType.WRITER for r in roles)

                # the groups are the ones defined in the LDAP server
                groups = {r.group.id: r.group.name for r in roles}
                assert groups == {
                    "groupA": "some group name",
                    "groupB": "some other group name",
                    "D": "isGroupD",  # use the configured mapping
                }

        finally:
            # Stop the mocked LDAP server when the test is finished.
            httpd.shutdown()
            httpd.server_close()
            server.join()
