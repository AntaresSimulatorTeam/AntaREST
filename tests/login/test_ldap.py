import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from antarest.common.config import Config, SecurityConfig
from antarest.login.ldap import AntaresUser, LdapService, AuthDTO
from antarest.login.model import UserCreateDTO, UserLdap


class MockServerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if "/auth" in self.path:
            content_length = int(self.headers["Content-Length"])
            print("data", content_length)
            data = self.rfile.read(content_length)
            print(data)
            create = AuthDTO.from_json(json.loads(data))
            print(create)
            antares = AntaresUser(
                first_name="Smith", last_name=create.user, groups=["group"]
            )
            res = json.dumps(antares.to_json())

            self.send_response(200)
            self.send_header("Content-Length", f"{len(res)}")
            self.end_headers()
            self.wfile.write(res.encode())


def test_ldap():
    config = Config(security=SecurityConfig(ldap_url="http://localhost:8868"))
    ldap = LdapService(config=config)

    # Start server
    httpd = HTTPServer(("localhost", 8868), MockServerHandler)
    server = threading.Thread(None, httpd.handle_request)
    server.start()

    res = ldap.auth(user=UserCreateDTO(name="John", password="pwd"))

    assert res
    assert "John Smith" == res.name
