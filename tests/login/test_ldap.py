import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import Mock

from antarest.core.config import Config, SecurityConfig, ExternalAuthConfig
from antarest.core.roles import RoleType
from antarest.login.ldap import ExternalUser, LdapService, AuthDTO
from antarest.login.model import UserLdap, Role, Group


class MockServerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if "/auth" in self.path:
            content_length = int(self.headers["Content-Length"])
            data = self.rfile.read(content_length)
            create = AuthDTO.from_json(json.loads(data))
            antares = ExternalUser(
                external_id=create.user,
                first_name="John",
                last_name="Smith",
                groups={
                    "groupA": "some group name",
                    "groupB": "some other group name",
                },
            )
            res = json.dumps(antares.to_json())

            self.send_response(200)
            self.send_header("Content-Length", f"{len(res)}")
            self.end_headers()
            self.wfile.write(res.encode())


def test_ldap():
    config = Config(
        security=SecurityConfig(
            external_auth=ExternalAuthConfig(
                url="http://localhost:8869", default_group_role=RoleType.WRITER
            )
        )
    )
    repo = Mock()
    repo.get_by_external_id.return_value = None
    repo.save.side_effect = lambda x: x
    group_repo = Mock()
    role_repo = Mock()
    ldap = LdapService(
        config=config, users=repo, groups=group_repo, roles=role_repo
    )

    # Start server
    httpd = HTTPServer(("localhost", 8869), MockServerHandler)
    server = threading.Thread(None, httpd.handle_request)
    server.start()

    role_repo.get_all_by_user.return_value = [Role(group_id="groupA")]
    group_repo.save.side_effect = lambda x: x
    role_repo.save.side_effect = lambda x: x

    res = ldap.login(name="extid", password="pwd")

    assert res
    assert "John Smith" == res.name
    assert "extid" == res.external_id
    repo.save.assert_called_once_with(
        UserLdap(
            name="John Smith",
            external_id="extid",
            firstname="John",
            lastname="Smith",
        )
    )
    group_repo.save.assert_called_once_with(
        Group(id="groupB", name="some other group name")
    )
    role_repo.save.assert_called_once_with(
        Role(
            identity=UserLdap(
                name="John Smith",
                external_id="extid",
                firstname="John",
                lastname="Smith",
            ),
            group=Group(id="groupB", name="some other group name"),
            type=RoleType.WRITER,
        )
    )
