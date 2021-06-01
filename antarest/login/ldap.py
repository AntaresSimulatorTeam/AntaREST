import logging
from typing import List, Optional

import requests
from dataclasses import dataclass

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.login.model import UserCreateDTO, UserLdap
from antarest.login.repository import UserLdapRepository

logger = logging.getLogger(__name__)


@dataclass
class AuthDTO:
    """
    Input LDAP data
    """

    user: str
    password: str

    @staticmethod
    def from_json(data: JSON) -> "AuthDTO":
        return AuthDTO(user=data["user"], password=data["password"])

    def to_json(self) -> JSON:
        return {"user": self.user, "password": self.password}


@dataclass
class AntaresUser:
    """
    Output LDAP data
    """

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
    """
    LDAP facade with connector to ldap server
    """

    def __init__(self, users: UserLdapRepository, config: Config):
        self.url = config.security.ldap_url
        self.users = users

    def _fetch(self, name: str, password: str) -> Optional[UserLdap]:
        """
        Fetch user from LDAP
        Args:
            name: username
            password: password

        Returns: User if connection success other Noen

        """
        if not self.url:
            return None

        auth = AuthDTO(user=name, password=password)
        try:
            res = requests.post(url=f"{self.url}/auth", json=auth.to_json())
        except Exception as e:
            logger.warning(
                "Failed to retrieve user from external auth service",
                exc_info=e,
            )
            return None
        if res.status_code != 200:
            return None

        antares_user = AntaresUser.from_json(res.json())  # TODO use ldap group
        return UserLdap(name=name)

    def _save(self, user: UserLdap) -> UserLdap:
        """
        Save user in db
        Args:
            user: user to save

        Returns:

        """
        return self.users.save(user)

    def get(self, id: int) -> Optional[UserLdap]:
        """
        Get User stored in DB
        Args:
            id: user id

        Returns: user

        """
        return self.users.get(id)

    def login(self, name: str, password: str) -> Optional[UserLdap]:
        """
        Try to log user to external LDAP
        Args:
            name: username
            password: password

        Returns: if logging success return a UserLDAP other None

        """
        user = self._fetch(name, password)
        if not user:
            return None

        return self.users.get_by_name(name) or self._save(UserLdap(name=name))

    def get_all(self) -> List[UserLdap]:
        """
        Get all users in DB.

        Returns: list of users

        """
        return self.users.get_all()

    def delete(self, id: int) -> None:
        """
        Delete user
        Args:
            id: user id to delete

        Returns:

        """
        return self.users.delete(id)
