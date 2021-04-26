from typing import List, Optional

import requests
from dataclasses import dataclass

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.login.model import UserCreateDTO, Password, UserLdap


@dataclass
class AuthDTO:
    user: str
    password: str

    @staticmethod
    def from_json(data: JSON) -> "AuthDTO":
        return AuthDTO(user=data["user"], password=data["password"])

    def to_json(self) -> JSON:
        return {"user": self.user, "password": self.password}


@dataclass
class AntaresUser:
    first_name: str
    last_name: str
    groups: List[str]

    @staticmethod
    def from_json(data: JSON) -> "AntaresUser":
        return AntaresUser(
            first_name=data["firstName"],
            last_name=data["lastName"],
            groups=data.get("groups", []),
        )

    def to_json(self) -> JSON:
        return {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "groups": self.groups,
        }


class LdapService:
    def __init__(self, config: Config):
        self.url = config.security.ldap_url

    def auth(self, user: UserCreateDTO) -> Optional[UserLdap]:
        if not self.url:
            return None

        auth = AuthDTO(user=user.name, password=user.password)
        res = requests.post(url=f"{self.url}/auth", json=auth.to_json())

        if res.status_code != 200:
            return None

        antares_user = AntaresUser.from_json(res.json())
        return UserLdap(
            name=f"{antares_user.last_name} {antares_user.first_name}",
        )
