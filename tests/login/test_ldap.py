import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import Mock

from antarest.common.config import Config, SecurityConfig
from antarest.login.ldap import AntaresUser, LdapService, AuthDTO
from antarest.login.model import UserCreateDTO, UserLdap


class MockServerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if "/auth" in self.path:
            content_length = int(self.headers["Content-Length"])
            data = self.rfile.read(content_length)
            create = AuthDTO.from_json(json.loads(data))
            antares = AntaresUser(
                first_name="Smith", last_name=create.user, groups=["group"]
            )
            res = json.dumps(antares.to_json())

            self.send_response(200)
            self.send_header("Content-Length", f"{len(res)}")
            self.end_headers()
            self.wfile.write(res.encode())


def test_ldap():
    config = Config(security=SecurityConfig(ldap_url="http://localhost:8869"))
    repo = Mock()
    repo.get_by_name.return_value = None
    repo.save.side_effect = lambda x: x
    ldap = LdapService(config=config, users=repo)

    # Start server
    httpd = HTTPServer(("localhost", 8869), MockServerHandler)
    server = threading.Thread(None, httpd.handle_request)
    server.start()

    res = ldap.login(name="John", password="pwd")

    assert res
    assert "John" == res.name
    repo.save.assert_called_once_with(UserLdap(name="John"))
